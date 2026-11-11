"""Canonical current raw/normalized/owner replay without proof-run seeds."""
from datetime import date, datetime
from app.services.bounded_financial_stock_owner import assemble as assemble_financial
from app.services.fresh_financial_stock_owner import fresh_stock_baseline
from app.services.sealed_fresh_dispatch import consume_bound_result, decode_request_plan
from app.services.sealed_native_bridge import require_complete_stock_window
from app.services.unified_aggregate_owners import us_market_aggregate_owner, kiwoom_aggregate_owner
from app.services.unified_aggregate_receipt import AggregateReceipt
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_source_composition import A, SourceInput, SourceRole
from app.services.unified_stock_acquisition import decode_owned_role
from app.services.unified_stock_anomaly_scope import materialize_source_components
import json

def read(path):
    return json.loads(path.read_bytes())

def bound(root, name):
    return dict(path=name, sha256=sha256_bytes((root/name).read_bytes()))

def require_captured_phase(root, frozen, outcome, phase):
    """Only a verified failed mandatory phase may enter ordinary INCOMPLETE."""
    state = outcome['phases'].get(phase, {})
    if state.get('status') != 'FAILED':
        return

    def checked_read(path):
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise OSError('captured_phase_symlink_denied')
        try:
            return read(path)
        except (ValueError, UnicodeError) as exc:
            raise OSError('captured_phase_malformed_receipt') from exc

    try:
        plan = decode_request_plan(frozen['plan'])
        proof = state['failure_provenance']
        if (checked_read(root/f'phase-{phase}.json') != state
                or proof['phase'] != phase or proof['generation_id'] != frozen['generation_id']
                or plan.generation_id != frozen['generation_id']
                or proof['plan_sha256'] != plan.plan_sha256 or not proof['failed_receipts']):
            raise OSError('captured_phase_provenance_mismatch')
        for key, receipt_sha in proof['failed_receipts'].items():
            descriptor = next((d for d in plan.descriptors if d.logical_request_id == key), None)
            if descriptor is None:
                raise OSError('captured_phase_unplanned_receipt')
            base = root/'dispatch/receipts'/key
            final = checked_read(base/'final.json')
            identity = dict(generation_id=plan.generation_id, logical_request_id=key,
                descriptor_sha256=descriptor.descriptor_sha256, plan_sha256=plan.plan_sha256,
                request_sha256=descriptor.request_semantic_sha256, role=descriptor.consumer_role)
            if (final != outcome['logical_results'][key] or final['status'] != 'FAILED'
                    or not final['attempts'] or not final.get('failure')
                    or final['receipt_sha256'] != receipt_sha
                    or digest({k:v for k,v in final.items() if k != 'receipt_sha256'}) != receipt_sha
                    or any(final.get(k) != v for k,v in identity.items())):
                raise OSError('captured_phase_receipt_identity_mismatch')
            for ordinal, attempt in enumerate(final['attempts'], 1):
                if (attempt['attempt'] != ordinal or checked_read(base/f'attempt-{ordinal}.json') != attempt
                        or any(attempt.get(k) != v for k,v in identity.items())):
                    raise OSError('captured_phase_attempt_mismatch')
                if attempt.get('artifact'):
                    raw_path = base/f'attempt-{ordinal}.body'
                    if (attempt['artifact'] != str(raw_path.relative_to(root/'dispatch'))
                            or any(p.is_symlink() for p in (raw_path, *raw_path.parents))
                            or sha256_bytes(raw_path.read_bytes()) != attempt['raw_sha256']):
                        raise OSError('captured_phase_raw_hash_mismatch')
                elif attempt.get('raw_sha256') is not None:
                    raise OSError('captured_phase_raw_missing')
    except (ValueError, KeyError, TypeError) as exc:
        raise OSError('captured_phase_invalid_provenance') from exc
    raise ValueError('SOURCE_PARTIAL:captured_phase_failure:' + phase)

def captured_phase_value(root, frozen, outcome, phase):
    """Captured is a prerequisite, not source-use or economic qualification."""
    require_captured_phase(root, frozen, outcome, phase)
    state = outcome['phases'].get(phase, {})
    if state.get('status') != 'CAPTURED_NOT_QUALIFIED':
        raise ValueError('SOURCE_PREREQUISITE_NOT_CAPTURED:' + phase)
    if 'value' not in state or state['value'] is None:
        raise ValueError('SOURCE_CAPTURE_VALUE_MISSING:' + phase)
    path = root / f'phase-{phase}.json'
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise OSError('captured_phase_symlink_denied')
    if read(path) != state:
        raise OSError('captured_phase_provenance_mismatch')
    return state['value']

def require_sealed_body(root, frozen, outcome, *, role, raw_sha256):
    plan = decode_request_plan(frozen['plan'])
    matches = [d for d in plan.descriptors if d.role_id == role
        and outcome['logical_results'].get(d.logical_request_id, {}).get('status') == 'PASS'
        and outcome['logical_results'][d.logical_request_id]['raw_sha256'] == raw_sha256]
    if not matches:
        raise ValueError('consumer_body_not_bound_to_sealed_role')
    for d in matches:
        consume_bound_result(root=root/'dispatch', plan=plan, logical_id=d.logical_request_id,
            receipt_sha256=outcome['logical_results'][d.logical_request_id]['receipt_sha256'])

def validate_subject_view(plan, subjects):
    """A subset cannot silently drop undeclared full-cohort issuer dependencies."""
    selected = None
    if subjects is not None:
        if (not isinstance(subjects, (tuple, list)) or not subjects
                or any(not isinstance(s, str) for s in subjects)):
            raise ValueError('stock_subject_view_invalid')
        selected = set(subjects)
        members = {t for tickers in plan.universe.values() for t in tickers}
        if len(selected) != len(subjects) or not selected <= members:
            raise ValueError('stock_subject_view_not_in_original_plan')
        if plan.contract == 'one-shot-stock-source-acquisition-v1' and selected != members:
            raise ValueError('stock_subject_view_full_cohort_dependency_contract_required')
    return selected


def current_local_seed(root, frozen, plan, market, policy, *, cycle_owner=None, prospective_owner=None, class_c_bridge=None):
    """Use the existing trusted freeze pin before interpreting local rows."""
    from app.services.selected_source_plan import SCOPE
    if frozen.get('scope') == SCOPE:
        if cycle_owner is not None or class_c_bridge is not None or market != plan.market:
            raise ValueError('selected_registration_original_memory_route_required')
        from app.services.selected_source_registration import local_seed
        return local_seed(prospective_owner, stock=plan, policy=policy)
    from app.services.unified_local_seed_bridge import admit_pinned_local_seed
    if class_c_bridge is not None:
        if cycle_owner is not None or prospective_owner is not None:
            raise ValueError('class_c_bridge_mixed_owner_route_denied')
        from app.services.current_class_c_source_bridge import memory_local_seed
        return memory_local_seed(class_c_bridge, frozen=frozen, plan=plan, market=market, policy=policy)
    name = f'class-c/local-{market}.json'
    pin = frozen.get('protected_input_hashes', {}).get(name)
    if not pin:
        raise ValueError('CURRENT_CLASS_C_SOURCE_UNAVAILABLE:independent_freeze_pin_missing')
    if (frozen['generation_id'] != plan.run_id
            or datetime.fromisoformat(frozen['frozen_at']) != plan.frozen_at):
        raise ValueError('class_c_frozen_generation_mismatch')
    sessions = {r.latest_completed_session for r in plan.reads if r.market == market}
    if len(sessions) != 1 or frozen['sessions'].get(market) not in sessions:
        raise ValueError('class_c_frozen_session_mismatch')
    path = root / name
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('class_c_source_symlink_denied')
    if cycle_owner is not None:
        from app.services.unified_cycle_owner import require_generation
        require_generation(cycle_owner, plan.run_id)
    if prospective_owner is not None:
        from app.services.prospective_class_c_owner import require_generation
        require_generation(prospective_owner, plan.run_id, purpose=frozen.get('execution_purpose'))
    return admit_pinned_local_seed(path.read_bytes(), expected_sha256=pin, market=market,
        session_key=next(iter(sessions)), cutoff=plan.frozen_at,
        subjects=plan.universe[market], policy=policy, cycle_owner=cycle_owner,
        prospective_owner=prospective_owner)

def stock_inputs(root, frozen, policy, outcome, *, subjects=None, cycle_owners=None, prospective_owners=None, class_c_bridge=None):
    from app.services.selected_source_plan import decode_stock_plan
    plan = decode_stock_plan(frozen)
    if class_c_bridge is not None:
        if cycle_owners is not None or prospective_owners is not None:
            raise ValueError('class_c_bridge_mixed_owner_route_denied')
        from app.services.current_class_c_source_bridge import require_dispatch, memory_owners
        require_dispatch(class_c_bridge, root=root, frozen=frozen, policy=policy)
        prospective_owners = memory_owners(class_c_bridge)
    selected = validate_subject_view(plan, subjects)
    native = root/'native/stocks'
    sealed = decode_request_plan(frozen['plan'])
    from app.services.completed_price_state import require_plan, bind_source
    from app.services.sealed_completed_price import replay_source
    require_plan(sealed, plan)
    results = outcome['logical_results']
    inputs, errors = {}, {}
    replay = read(root/'native/raw-owner-replay.json')
    if len(replay) != len(plan.reads) or any(r['status'] != 'PASS' for r in replay):
        raise ValueError('SOURCE_PARTIAL:native_raw_owner_replay')
    window = dict(run_id=plan.run_id, collection_started_at=frozen['frozen_at'],
        source_query_cutoff=frozen['frozen_at'], business_availability_cutoff=outcome['completed_at'])
    for market, tickers in plan.universe.items():
        for ticker in tickers:
            if selected is not None and ticker not in selected:
                continue
            try:
                local = current_local_seed(root, frozen, plan, market, policy,
                    cycle_owner=(cycle_owners or {}).get(market),
                    prospective_owner=None if class_c_bridge is not None else (prospective_owners or {}).get(market),
                    class_c_bridge=class_c_bridge)
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
                session = next(r.latest_completed_session for r in plan.reads if r.subject == ticker)
                components = materialize_source_components(ticker=ticker, market=market, cutoff=date.fromisoformat(session),
                    observed_at=plan.frozen_at.isoformat(), roles=roles, completed_session=market == "kr")
                technical = dict(plan=plan, ticker=ticker, local_seed=local, financial=None,
                    receipts=receipts, artifacts=artifacts, components=components, policy=policy,
                    expected_hashes=dict(plan=digest(plan.model_dump(mode='json')), local=digest(local),
                        financial=digest(None), receipts=digest(receipts), components=digest(components)))
                if (cycle_owners or {}).get(market) is not None:
                    technical['cycle_owner'] = cycle_owners[market]
                if (prospective_owners or {}).get(market) is not None:
                    technical['prospective_owner'] = prospective_owners[market]
                    technical['execution_purpose'] = frozen.get('execution_purpose')
                if market == 'us':
                    daily = next(r for r in plan.reads if r.subject == ticker and r.role == 'adjusted_daily')
                    close_input = replay_source(root=root, frozen=frozen, outcome=outcome, read=daily)
                    technical = bind_source(technical, security=frozen['candidate']['financial_plans'][ticker]['security'],
                                            **close_input)
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
                # Both full and selected cohorts enter the same existing
                # comparison owner. It replays raw/PIT/quality before issuing
                # any business-use projection; the opt-in is not a use grant.
                item['reported_comparison_business']=True
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
    if frozen.get('scope')!='SELECTED_ORIGINAL_RESEARCH_V1' and 'SKHY' in inputs and '000660' in inputs:
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
        require_captured_phase(root, frozen, outcome, market+'-market')
        path = root/'markets'/market
        try:
            at = datetime.fromisoformat(read(root/'markets'/f'{market}-query.json')['observed_at'])
        except (ValueError, KeyError, TypeError) as exc:
            raise OSError('market_query_receipt_corrupt') from exc
        role = SourceRole(key='us_market_prices' if market == 'us' else 'kr_local_indices_sectors_breadth',
            owner='us_market' if market == 'us' else 'kiwoom_pages', market=market, symbol='*',
            provider='ohlcv_analyst' if market == 'us' else 'kiwoom_rest', basis='adjusted_close' if market == 'us' else 'query_time',
            session=frozen['sessions'][market], acquisition_class=A, mandatory=True)
        if market == 'us':
            commands = [read(p) for p in (root/'native').glob('command-*.json')]
            sealed = decode_request_plan(frozen['plan'])
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
    selected=frozen.get('scope')=='SELECTED_ORIGINAL_RESEARCH_V1'
    kr=selected and frozen['selected_market']=='kr'
    providers = ('ecos',) if frozen.get('scope') == 'KR8_ONLY' or kr else ('fred', 'eia', 'ecos')
    for provider in providers:
        captured_phase_value(root, frozen, outcome, provider)
    night_value = None if kr and not frozen['candidate']['night_query_dates'] else captured_phase_value(root, frozen, outcome, 'night')
    def captured(path, provider, acquisition=None):
        rows = [read(p) for p in sorted(path.glob('receipt-*.json'))]
        sealed = decode_request_plan(frozen['plan'])
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
        providers={p: captured(root/'publications'/p, p) for p in providers}, policy=policy)
    if frozen.get('scope') in {'KR8_ONLY','US14_ONLY'}:
        publications['market_scope'] = frozen['scope']
    if selected:
        publications['market_scope']='SELECTED_'+frozen['selected_market'].upper()
    if night_value is None:
        return dict(publications=publications,night=None)
    night_id = frozen['generation_id']+':night'
    probe = captured(root/'night/probe', 'krx_night_futures', night_id)
    history = captured(root/'night/history', 'krx_night_futures', night_id)
    probe['bodies'].update(history['bodies'])
    probe['body_hashes'].update(history['body_hashes'])
    night = dict(**probe, history_receipts=history['receipts'], observed_at=start, run_id=frozen['generation_id'],
        acquisition_id=night_id, expected_value_sha256=digest(night_value), policy=policy,
        run_started_at=start, acquisition_cutoff=cutoff)
    return dict(publications=publications, night=night)
