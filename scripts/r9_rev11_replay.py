"""Receipt-bound all-source materialization, with external network disabled."""
from datetime import date, datetime
import json
from pathlib import Path

from app.services.bounded_financial_stock_owner import assemble as assemble_financial
from app.services.fresh_financial_stock_owner import assemble_fresh_stock, fresh_stock_baseline
from app.services.fresh_publication_replay import replay_fresh_publications
from app.services.sealed_fresh_dispatch import consume_bound_result, ProviderPlan
from app.services.sealed_native_bridge import require_complete_stock_window
from app.services.unified_aggregate_owners import us_market_aggregate_owner, kiwoom_aggregate_owner
from app.services.unified_aggregate_receipt import AggregateReceipt
from app.services.unified_full_source_cohort import FreshFullSourceRunSeed, compose_full_source
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_sealed_context import replay_night
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_source_composition import A, SourceInput, SourceRole, _resolve
from app.services.unified_stock_acquisition import StockPlan, decode_owned_role
from app.services.unified_stock_anomaly_scope import materialize_source_components
from scripts.r2b_r9_full_fresh_requalification import fresh_authority_inputs


def read(path):
    return json.loads(path.read_bytes())


def bound(root, name):
    return dict(path=name, sha256=sha256_bytes((root/name).read_bytes()))


def require_sealed_body(root, frozen, outcome, *, role, raw_sha256):
    plan = ProviderPlan.model_validate(frozen['plan'])
    matches = [d for d in plan.descriptors if d.role_id == role
        and outcome['logical_results'].get(d.logical_request_id, {}).get('status') == 'PASS'
        and outcome['logical_results'][d.logical_request_id]['raw_sha256'] == raw_sha256]
    if not matches:
        raise ValueError('consumer_body_not_bound_to_sealed_role')
    for d in matches:
        consume_bound_result(root=root/'dispatch', plan=plan, logical_id=d.logical_request_id,
            receipt_sha256=outcome['logical_results'][d.logical_request_id]['receipt_sha256'])


def stock_inputs(root, frozen, policy, outcome):
    plan = StockPlan.model_validate(frozen['stock_plan'])
    native = root/'native/stocks'
    sealed = ProviderPlan.model_validate(frozen['plan'])
    results = outcome['logical_results']
    inputs, errors = {}, {}
    replay = read(root/'native/raw-owner-replay.json')
    if len(replay) != len(plan.reads) or any(r['status'] != 'PASS' for r in replay):
        raise ValueError('SOURCE_PARTIAL:native_raw_owner_replay')
    window = dict(run_id=plan.run_id, collection_started_at=frozen['frozen_at'],
        source_query_cutoff=frozen['frozen_at'], business_availability_cutoff=outcome['completed_at'])
    for market, tickers in plan.universe.items():
        for ticker in tickers:
            try:
                receipts, artifacts, roles = {}, {}, {}
                for ordinal, entry in enumerate(plan.reads, 1):
                    if entry.subject != ticker:
                        continue
                    r = read(native/f'role-{ordinal:03d}.receipt.json')
                    def source(name, sha):
                        raw = (native/name).read_bytes()
                        if sha256_bytes(raw) != sha:
                            raise ValueError('native_artifact_hash_mismatch')
                        artifacts[name] = raw
                        return raw
                    rows = decode_owned_role(plan, entry, r, source)
                    require_complete_stock_window(entry, r, rows)
                    for i, page in enumerate(r['pages'], 1):
                        key = entry.entry_id + ':page1' + (':continuation:' + str(i) if i > 1 else '')
                        final = results[key]
                        consume_bound_result(root=root/'dispatch', plan=sealed, logical_id=key, receipt_sha256=final['receipt_sha256'])
                        if page['source_sha256'] != final['raw_sha256']:
                            raise ValueError('native_page_not_same_sealed_response')
                    receipts[entry.role], roles[entry.role] = r, rows
                local = read(root/f'class-c/local-{market}.json')
                session = next(r.latest_completed_session for r in plan.reads if r.subject == ticker)
                components = materialize_source_components(ticker=ticker, market=market, cutoff=date.fromisoformat(session),
                    observed_at=plan.frozen_at.isoformat(), roles=roles, completed_session=market == "kr")
                technical = dict(plan=plan, ticker=ticker, local_seed=local, financial=None,
                    receipts=receipts, artifacts=artifacts, components=components, policy=policy,
                    expected_hashes=dict(plan=digest(plan.model_dump(mode='json')), local=digest(local),
                        financial=digest(None), receipts=digest(receipts), components=digest(components)))
                path = root/'financial'/ticker
                financial_receipts = read(path/'owner-receipts.json')
                for receipt in financial_receipts:
                    key = receipt['sealed_logical_id']
                    final = results[key]
                    if (receipt['sealed_generation_id'] != plan.run_id or receipt['sealed_final_receipt_sha256'] != final['receipt_sha256']):
                        raise ValueError('financial_sealed_receipt_mismatch')
                    if final['status'] == 'PASS':
                        consume_bound_result(root=root/'dispatch', plan=sealed, logical_id=key, receipt_sha256=final['receipt_sha256'])
                item = dict(technical_inputs=technical, financial_inputs=dict(plan=frozen['candidate']['financial_plans'][ticker],
                    acquisition=read(path/'owner-acquisition.json'), receipts=financial_receipts, directory=path, field_semantics=True), source_window=window)
                if frozen.get('valuation_slots'):
                    from app.services.provider_native_valuation_acquisition import replay_native
                    item['valuation_inputs'] = replay_native(root=root, frozen=frozen, outcome=outcome,
                        security=frozen['candidate']['financial_plans'][ticker]['security'], policy=policy)
                event = root/'events'/ticker/'bound-source.json'
                if event.exists():
                    for p in event.parent.glob('*.response.json'):
                        r = read(p)
                        if r.get('artifact'):
                            require_sealed_body(root, frozen, outcome, role='events:'+ticker,
                                raw_sha256=sha256_bytes((p.parent/r['artifact']).read_bytes()))
                    item['event_inputs'] = dict(acquisition_class='FRESH_CURRENT_RUN', window=window, source=read(event))
                else:
                    raise ValueError("SOURCE_PARTIAL:event_owned_current_state_missing")
                inputs[ticker] = item
            except (ValueError, KeyError, TypeError, OSError) as exc:
                errors[ticker] = dict(error_class=type(exc).__name__, reason=str(exc))
    if 'SKHY' in inputs and '000660' in inputs:
        source = inputs['000660']
        source_owner = dict(baseline=fresh_stock_baseline(source['technical_inputs']),
            local_seed=source['technical_inputs']['local_seed'], **source['financial_inputs'])
        official = read(root/'static/official-security-identity.json')
        inputs['SKHY']['financial_inputs']['issuer_business'] = dict(source_inputs=source_owner,
            official_identity=official, official_identity_sha256=digest(official), source_result_sha256=digest(assemble_financial(**source_owner)))
    if frozen.get('scope') == 'US14_ONLY' and 'SKHY' in inputs:
        from app.services.bounded_financial_stock_owner import replay_issuer_source
        path = root/'financial/000660'
        try:
            receipts = read(path/'owner-receipts.json')
            for receipt in receipts:
                key = receipt['sealed_logical_id']
                final = results[key]
                if (receipt['sealed_generation_id'] != plan.run_id
                        or receipt['sealed_final_receipt_sha256'] != final['receipt_sha256']):
                    raise ValueError('auxiliary_sealed_receipt_mismatch')
                if final['status'] == 'PASS':
                    consume_bound_result(root=root/'dispatch', plan=sealed, logical_id=key,
                        receipt_sha256=final['receipt_sha256'])
            source_owner = dict(plan=frozen['candidate']['financial_plans']['000660'],
                acquisition=read(path/'owner-acquisition.json'),receipts=receipts,directory=path,
                field_semantics=True,dependency=frozen['candidate']['auxiliary_issuer_dependencies']['000660'])
            target = inputs['SKHY']['financial_inputs']['plan']
            source = replay_issuer_source(source_owner, target_plan=target)
            official = read(root/'static/official-security-identity.json')
            inputs['SKHY']['financial_inputs']['issuer_business'] = dict(source_inputs=source_owner,
                official_identity=official,official_identity_sha256=digest(official),source_result_sha256=digest(source))
        except (ValueError,KeyError,TypeError,OSError) as exc:
            errors['SKHY:auxiliary:000660'] = dict(error_class=type(exc).__name__,reason=str(exc))
    return inputs, errors


def aggregate(root, role, value):
    plan = read(root/'plan.json')
    children, times = [], []
    for path in sorted(root.glob('*.response.json')):
        stem = path.name.removesuffix('.response.json')
        r = read(path)
        times.append((r['requested_at'], r['received_at']))
        children.append(dict(child_id=stem, receipt=bound(root, path.name),
            normalization=bound(root, stem+'.normalization.json') if (root/(stem+'.normalization.json')).exists() else None,
            accepted_page=bound(root, stem+'.page.json') if (root/(stem+'.page.json')).exists() else None))
    if not children:
        raise ValueError('market_children_missing')
    from app.services.kiwoom_consumed_page_contract import CONTRACT as KR_CONSUMED_CONTRACT
    values = dict(owner=role.owner, role=role.key, market=role.market, provider=role.provider, symbol=role.symbol,
        basis=role.basis, session=role.session, run_id=plan['run_id'], attempt_id=plan['attempt_id'], acquisition_id=None,
        acquisition_class=A.value, requested_at=min(t[0] for t in times), received_at=max(t[1] for t in times),
        artifact='aggregate-value.json', artifact_sha256=sha256_bytes(encoded(value)+b'\n'), plan=bound(root,'plan.json'),
        children=children, expected_child_ids=[c['child_id'] for c in children], normalized_sha256=digest(value),
        validator_contract=(KR_CONSUMED_CONTRACT if role.key == 'kr_local_indices_sectors_breadth'
                            else 'sealed-fresh-native-owner-aggregate-v1'), coverage=dict(children=len(children)),
        contract='unified-transitive-source-receipt-v1')
    receipt = AggregateReceipt.model_validate({**values, 'aggregate_sha256': digest(values)})
    for name, obj in [('aggregate-value.json', value), ('aggregate.json', receipt.model_dump(mode='json'))]:
        path = root/name
        if path.exists():
            if path.read_bytes() != encoded(obj)+b'\n':
                raise ValueError('market_replay_materialization_drift')
        else:
            durable_json(path, obj, exclusive=True)
    return receipt


def market_inputs(root, frozen, outcome, policy):
    result = {}
    for market in frozen['sessions']:
        path = root/'markets'/market
        at = datetime.fromisoformat(read(root/'markets'/f'{market}-query.json')['observed_at'])
        role = SourceRole(key='us_market_prices' if market == 'us' else 'kr_local_indices_sectors_breadth',
            owner='us_market' if market == 'us' else 'kiwoom_pages', market=market, symbol='*',
            provider='ohlcv_analyst' if market == 'us' else 'kiwoom_rest', basis='adjusted_close' if market == 'us' else 'query_time',
            session=frozen['sessions'][market], acquisition_class=A, mandatory=True)
        if market == 'us':
            commands = [read(p) for p in (root/'native').glob('command-*.json')]
            sealed = ProviderPlan.model_validate(frozen['plan'])
            for response in path.glob('*.response.json'):
                r = read(response)
                body = read(path/r['artifact'])
                matches = [c for c in commands if c['command'] == {'market': r['symbol']}
                    and c['result_sha256'] == digest(dict(status=r['http_status'], body=body))
                    and c['generation_id'] == frozen['generation_id']
                    and c['native_input_sha256'] == sha256_bytes((root/'native-input.json').read_bytes())]
                if len(matches) != 1 or not matches[0]['sealed_receipts']:
                    raise ValueError('native_market_command_binding_missing')
                for key, sha in matches[0]['sealed_receipts'].items():
                    consume_bound_result(root=root/'dispatch', plan=sealed, logical_id=key, receipt_sha256=sha)
            value = outcome['phases']['us-market']['value']
            owner = us_market_aggregate_owner(role=role, source_url=frozen['ohlcv_source_url'], policy=policy)
        else:
            for response in path.glob('*.response.json'):
                r = read(response)
                require_sealed_body(root, frozen, outcome, role='kr_market:'+r['read_key'],
                    raw_sha256=sha256_bytes((path/r['artifact']).read_bytes()))
            n = read(path/'normalization.json')
            if not n['mandatory_complete']:
                raise ValueError('SOURCE_PARTIAL:kr_market_consumer_incomplete')
            value = n['roles'][role.key]['value']
            owner = kiwoom_aggregate_owner(role=role, observed_at=at, max_pages=frozen['kr_local_cap'],
                max_requests_per_page=1, policy=policy, consumer_complete=True)
        receipt = aggregate(path, role, value)
        item = SourceInput(role=role.key, run_id=receipt.run_id, attempt_id=receipt.attempt_id, acquisition_class=A,
            requested_at=receipt.requested_at, received_at=receipt.received_at, artifact=receipt.artifact,
            artifact_sha256=receipt.artifact_sha256, receipt_artifact='aggregate.json', receipt_sha256=bound(path,'aggregate.json')['sha256'])
        result[market] = dict(native_aggregate=dict(item=item, role=role, root=path, run_id=frozen['generation_id'],
            start=datetime.fromisoformat(frozen['frozen_at']), cutoff=datetime.fromisoformat(outcome['completed_at']),
            attempt_id=receipt.attempt_id, policy=policy, owners={role.owner: owner}))
    return result


def publication_inputs(root, frozen, outcome, policy):
    def captured(path, provider, acquisition=None):
        rows = [read(p) for p in sorted(path.glob('receipt-*.json'))]
        sealed = ProviderPlan.model_validate(frozen['plan'])
        for row in rows:
            final = outcome['logical_results'][row['sealed_logical_id']]
            if row['sealed_final_receipt_sha256'] != final['receipt_sha256']:
                raise ValueError('publication_sealed_receipt_mismatch')
            if final['status'] == 'PASS':
                consume_bound_result(root=root/'dispatch', plan=sealed, logical_id=row['sealed_logical_id'],
                    receipt_sha256=final['receipt_sha256'])
                if final['raw_sha256'] != row['artifact_sha256']:
                    raise ValueError('publication_sealed_body_mismatch')
        if acquisition:
            rows = [dict(r, acquisition_id=acquisition) for r in rows]
        bodies = {r['artifact']: (root/'dispatch'/r['artifact']).read_bytes() for r in rows}
        return dict(receipts=rows, bodies=bodies, body_hashes={k: sha256_bytes(v) for k, v in bodies.items()})
    start, cutoff = datetime.fromisoformat(frozen['frozen_at']), datetime.fromisoformat(outcome['completed_at'])
    publications = dict(run_id=frozen['generation_id'], run_started_at=start, acquisition_cutoff=cutoff, as_of=start,
        providers={p: captured(root/'publications'/p, p) for p in
            (('ecos',) if frozen.get('scope') == 'KR8_ONLY' else ('fred', 'eia', 'ecos'))}, policy=policy)
    if frozen.get('scope') in {'KR8_ONLY','US14_ONLY'}:
        publications['market_scope'] = frozen['scope']
    night_id = frozen['generation_id']+':night'
    probe = captured(root/'night/probe', 'krx_night_futures', night_id)
    history = captured(root/'night/history', 'krx_night_futures', night_id)
    probe['bodies'].update(history['bodies'])
    probe['body_hashes'].update(history['body_hashes'])
    night = dict(**probe, history_receipts=history['receipts'], observed_at=start, run_id=frozen['generation_id'],
        acquisition_id=night_id, expected_value_sha256=digest(outcome['phases']['night']['value']), policy=policy,
        run_started_at=start, acquisition_cutoff=cutoff)
    return dict(publications=publications, night=night)


def whole_inputs(root, frozen, outcome, policy):
    if frozen.get('scope') == 'US14_ONLY':
        from scripts.us14_source_scope import require_us14_plan
        require_us14_plan(frozen)
    if frozen.get('scope') == 'KR8_ONLY':
        from scripts.kr8_source_scope import require_kr8_plan
        require_kr8_plan(frozen)
    inputs, errors = stock_inputs(root, frozen, policy, outcome)
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
    markets = market_inputs(root, frozen, outcome, policy)
    context = publication_inputs(root, frozen, outcome, policy)
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
    versions = {f'class-c/local-{m}.json': sha256_bytes((root/f'class-c/local-{m}.json').read_bytes()) for m in universe}
    repo = Path(__file__).resolve().parents[1]
    inventory = read(repo/'docs/operations/UNIFIED_ACQUISITION_CLASSES.json')
    from app.services.whole_source_code_owner_registry import WholeSourceCodeOwnerRegistry
    registry = WholeSourceCodeOwnerRegistry.freeze(repo,
        profile='fresh_us14' if frozen.get('scope')=='US14_ONLY' else 'fresh' if 'us' in universe else 'fresh_kr8')
    denials = dict(kr_market_investor_flows=dict(status='OPTIONAL_UNAVAILABLE', value=None,
        denial='NOT_SELECTED_FOR_MARKET_COMPOSITION', run_id=frozen['generation_id']))
    bridge = rows['SKHY']['issuer_business_bridge'] if 'us' in universe else {'status': 'NOT_APPLICABLE_KR8_ONLY'}
    bindings = {t: digest(dict(technical_plan=plan.model_dump(mode='json'),financial_plan=i['financial_inputs']['plan'])) for t,i in inputs.items()}
    from app.services.unified_full_source_cohort import FreshKRSourceRunSeed, FreshUSSourceRunSeed, auxiliary_issuer_binding
    seed_type = FreshUSSourceRunSeed if frozen.get('scope')=='US14_ONLY' else FreshFullSourceRunSeed if 'us' in universe else FreshKRSourceRunSeed
    auxiliary = {'auxiliary_issuer_set_sha256':digest(auxiliary_issuer_binding(
        {t:dict(fresh_financial_binding=i) for t,i in inputs.items()}))} if seed_type is FreshUSSourceRunSeed else {}
    seed = seed_type(proof_mode='AD_HOC_LIVE_SOURCE_PROOF', packet_scope='LIVE_SOURCE_ADAPTER_PROOF_NOT_PRODUCTION_DECISION',
        parent_run_id=plan.run_id, started_at=plan.frozen_at, source_policy_sha256=digest(sorted(policy.allowed_providers)),
        inventory_sha256=digest(inventory), **registry.seed_bindings, universe_sha256=digest(universe),
        attempts={m:n['attempt_id'] for m,n in native.items()}, attempt_hashes={m:digest(n) for m,n in native.items()},
        run_acquisitions=dict(stock=digest(plan.model_dump(mode='json')),publications=digest(pub),night=night['value_sha256']),
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


def replay_twice(root, frozen, outcome, policy):
    args = whole_inputs(root, frozen, outcome, policy)
    first, second = compose_full_source(**args), compose_full_source(**args)
    if first != second:
        raise ValueError('whole_source_replay_drift')
    from app.services.whole_source_code_owner_registry import replay_identity_receipt
    identity = replay_identity_receipt(Path(__file__).resolve().parents[1], seed=args['seed'],
        metadata=args['composition_metadata'], first=first, second=second)
    from app.services.provider_valuation_calibration_context import calibration_context
    def contexts(whole):
        return {t: calibration_context(s['valuation_view']) for packet in whole['packets'].values()
            for t, s in packet['stocks'].items()}
    first_contexts, second_contexts = contexts(first), contexts(second)
    if first_contexts != second_contexts:
        raise ValueError('valuation_b_context_replay_drift')
    return args, first, dict(first_sha256=digest(first), second_sha256=digest(second), replay_equal=True,
                            code_owner_registry_identity=identity,
                            valuation_b_context_sha256=digest(first_contexts))
