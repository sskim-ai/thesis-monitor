"""Manual vNext-only CLI. Importing this module does not open a DB or Settings."""
import argparse
import json

from app.services.vnext_runtime import RuntimeConfig, VNextRuntime


def run_reviewed_product(config, ticker, **kwargs):
    """Backend-only manual entry point; JSON cannot supply the review callback."""
    return VNextRuntime(config).research_product(ticker, **kwargs)


def run_no_send_slot(config, **kwargs):
    """Explicit isolated backend capability; no scheduler or JSON Owner input."""
    from app.services.vnext_no_send_runner import run_slot
    return run_slot(config, **kwargs)


def run_manual_research_canary(config, **kwargs):
    """Explicit trusted backend only; no CLI scheduler or public job loader."""
    from app.services.vnext_no_send_runner import run_manual_research
    return run_manual_research(config, **kwargs)


def run_daily_research(config, *, bridge, identity, manual_scope=None,
                       allow_capture=False, allow_primary=False, expected_packet_sha256=None,
                       execution_authority=None, unified_review=None, unified_enabled=False, **kwargs):
    """Join original source, cold consumer and Primary inside the existing host.

    The live bridge is a backend capability. This does not install a schedule,
    grant HTTP/model permission or deserialize public JSON into an Owner.
    """
    from app.services.vnext_daily_bridge import DailyResearchBridge
    if not isinstance(bridge, DailyResearchBridge):
        raise ValueError('daily_bridge_backend_required')
    if kwargs.get('initialization_recovery') is not None and (
            manual_scope is None or allow_capture or not allow_primary):
        raise ValueError('daily_recovery_model_only_no_capture')
    if identity['security'] != bridge.registration['security']['canonical_security_id']:
        raise ValueError('daily_bridge_host_security')
    def operation(controller, gate):
        if (gate['session'] != bridge.session or
                gate['market'] != bridge.registration['security']['country'].lower() or
                manual_scope is not None and (gate['prior_session'] != bridge.prior_session or
                    gate['plan_sha256'] != bridge.request['plan_sha256'])):
            raise ValueError('daily_bridge_host_session_or_plan')
        result = bridge.execute(controller, allow_capture=allow_capture, allow_primary=allow_primary,
            execution_authority=execution_authority, unified_review=unified_review, unified_enabled=unified_enabled)
        if (expected_packet_sha256 is not None and result.get('packet_sha256') is not None
                and result['packet_sha256'] != expected_packet_sha256):
            raise ValueError('daily_bridge_frozen_packet_drift')
        return dict(result, input_identity=identity, send=False)
    if manual_scope is not None:
        return run_manual_research_canary(config, scope=manual_scope, identity=identity,
            operation=operation, **kwargs)
    return run_no_send_slot(config, identity=identity, operation=operation, **kwargs)


def run_unified_no_send(controller, *, packet, owner, mode, output_context, enabled=False):
    """Same callable for dated replay and daily; no model, capture or schedule."""
    from app.services.vnext_unified_dispatch import consume
    return consume(controller,packet=packet,owner=owner,mode=mode,
                   output_context=output_context,enabled=enabled)


def run_daily_no_send(config, **kwargs):
    """Operator entrypoint, default OFF; never installs a scheduler or sender."""
    from app.services.vnext_daily_entrypoint import run_daily
    return run_daily(config, **kwargs)


def cold_registered_valuation_source(root, *, expected_replay_sha256):
    """Original source replay only; no live Owner reconstruction or DB open."""
    from app.services.vnext_research_store import plain,digest
    from app.services.provider_native_valuation_acquisition import replay_native
    from app.services.provider_native_valuation_snapshot import derive_provider_snapshots
    from app.services.unified_source_policy import UnifiedSourcePolicy
    root=plain(root);raw=plain(root/'original-replay.json').read_bytes()
    if digest(raw)!=expected_replay_sha256:
        raise ValueError('valuation_runner_replay_hash_changed')
    data=json.loads(raw);rows=[]
    from app.services.sealed_fresh_dispatch import decode_request_plan,_binding_parent
    plan=decode_request_plan(data['frozen']['plan'])
    outcome=dict(data['outcome'],logical_results=dict(data['outcome']['logical_results']))
    no_io=[]
    for key,result in data['outcome']['logical_results'].items():
        if result.get('status')!='NOT_SELECTED':continue
        # Original atomic replay expects only attempted pages. Verify every
        # original no-I/O binding before projecting it out, without editing the
        # persisted dispatcher outcome or turning a selected failure into absence.
        decision=_binding_parent(root/'dispatch',plan,key,result['receipt_sha256'])
        if decision.get('status')!='NOT_SELECTED':
            raise ValueError('valuation_runner_no_io_binding_required')
        no_io.append(dict(logical_id=key,receipt_sha256=result['receipt_sha256']))
        del outcome['logical_results'][key]
    for security in data['securities']:
        inputs=replay_native(root=root,frozen=data['frozen'],outcome=outcome,security=security,
            policy=UnifiedSourcePolicy(frozenset({'kiwoom_rest','finnhub'})))
        if inputs.get('contract')=='provider-native-valuation-unavailable-v1':
            rows.append(dict(ticker=security['ticker'],status='UNAVAILABLE',reason=inputs['reason'],metrics=[]))
        else:
            metrics=derive_provider_snapshots(inputs,security=security,run_id=data['frozen']['generation_id'])
            rows.append(dict(ticker=security['ticker'],status='ORIGINAL_ATOMIC_REPLAY',
                metrics=[m.model_dump(mode='json') for m in metrics]))
    return dict(contract='registered-valuation-source-cold-v1',rows=rows,verified_no_io=no_io,
        current_economic_owner=False,strict_ready=False,send=False)


async def run_registered_valuation_source(*, preflight, base, external_root,
        acquire_current_context=None, load_credentials=None, inner=None, enabled=False):
    """Existing worker entry -> C18 prewire -> original private capture -> Cold.

    Backend callbacks are not CLI/JSON grants. Static inputs are checked before
    any callback, credentials, Parent or Worker. Source ratios grant no economy.
    """
    import asyncio,os,sys
    from datetime import datetime,timezone
    from pathlib import Path
    from app.services.valuation_research_preflight import prepare_registered_valuation
    from app.services.vnext_research_store import digest,encoded,plain
    if enabled is not True:
        raise ValueError('valuation_runner_explicit_enable_required')
    pins={str(p):digest(p.read_bytes()) for p in (Path(__file__),
        Path(__file__).parent/'services/valuation_research_preflight.py',
        Path(__file__).parent/'services/retained_identity_routing.py')}
    if set(preflight)!={'routing_root','identities','generation_id','cutoff','code_sha','provider_config_sha256'}:
        raise ValueError('valuation_runner_exact_preflight_required')
    context={}
    def backend():
        if (not callable(acquire_current_context) or not callable(load_credentials)
                or inner is None or not callable(getattr(inner,'handle_async_request',None))
                or not Path(external_root).is_dir() or Path(external_root).is_symlink()):
            raise ValueError('valuation_runner_authorized_credentials_transport_required')
        for path,sha in pins.items():
            if digest(Path(path).read_bytes())!=sha:
                raise ValueError('valuation_runner_code_changed')
        context.update(acquire_current_context())
        return context
    prepared=prepare_registered_valuation(**preflight,enabled=True,
        acquire_current_context=backend if acquire_current_context is not None else None)
    if prepared['parent'] is None:
        return dict(status='NO_LIVE_NEW_OWNER',preflight=prepared['receipt'],
            physical_HTTP=0,models=0,send=False)
    if not callable(load_credentials) or inner is None:
        raise ValueError('valuation_runner_authorized_credentials_transport_required')
    for path,sha in pins.items():
        if digest(Path(path).read_bytes())!=sha:
            raise ValueError('valuation_runner_code_changed')
    from app.services.market_component_execution import prepare_capture
    from app.services.market_worker_rpc import MarketWorkerRPC
    from app.providers.kiwoom_rest_client import KiwoomRestClient
    from app.services.provider_native_valuation_acquisition import collect_native
    from app.services.sealed_response_binding import SlotNotSelected
    credentials=load_credentials()
    if set(credentials)!={'app_key','secret_key'} or not all(isinstance(v,str) and v for v in credentials.values()):
        raise ValueError('valuation_runner_original_settings_credentials_required')
    wire=prepared['wire'];run=transport=worker=None;base=plain(base)
    try:
        run,transport,worker,_=prepare_capture(parent=prepared['parent'],wire=wire,
            session=context['session'],base=base,credentials=credentials,inner=inner,
            external_root=external_root,valuation_only=True)
        client=KiwoomRestClient(**credentials,max_retries=0,request_interval_seconds=1.5,
            transport=MarketWorkerRPC(worker))
        await asyncio.wait_for(collect_native(frozen={'valuation_slots':wire['valuation_slots']},
            settings=None,sealed=None,client=client),timeout=240)
        for descriptor in run.plan.descriptors:
            key=descriptor.logical_request_id
            if key in run.used:continue
            try:request,_,_=run.resolve(key)
            except SlotNotSelected:run.skip_unselected(key);continue
            reply=await worker.command({'market_wire':dict(logical_id=key,request_json=request)})
            if reply.get('status')!=200:
                raise ValueError('valuation_runner_selected_page_denied')
        data=dict(securities=list(preflight['identities'].values()),frozen=dict(
            plan=run.plan.model_dump(mode='json'),generation_id=run.plan.generation_id,
            frozen_at=run.plan.frozen_at.isoformat(),valuation_slots=wire['valuation_slots']),
            outcome=dict(logical_results=run.results,completed_at=datetime.now(timezone.utc).isoformat()))
        raw=encoded(data)
        fd=os.open(base/'original-replay.json',os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    finally:
        if worker is not None:await worker.shutdown()
        if transport is not None:await transport.shutdown()
    process=await asyncio.create_subprocess_exec(sys.executable,'-B','-m','app.vnext_worker',
        'valuation-source-cold','--source-root',str(base),'--replay-sha256',digest(raw),
        stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,cwd=Path(__file__).resolve().parents[1])
    stdout,stderr=await asyncio.wait_for(process.communicate(),timeout=60)
    if process.returncode:
        raise ValueError('valuation_runner_separate_cold_failed:'+digest(stderr))
    cold=json.loads(stdout)
    if cold!=cold_registered_valuation_source(base,expected_replay_sha256=digest(raw)):
        raise ValueError('valuation_runner_separate_cold_changed')
    return dict(status='ORIGINAL_SOURCE_CAPTURE_AND_SEPARATE_COLD',preflight=prepared['receipt'],
        physical_attempts=run.physical_attempts,worker_returncode=worker.process.returncode,
        replay_sha256=digest(raw),cold=cold,source_only=True,send=False,current_economic_owner=False)


def _mac_valuation_session():
    from app.services.kiwoom_participant_session import ParticipatingSession
    from app.services import (kiwoom_global_lane,kiwoom_participant_session,
        current_scoped_worker_bridge,current_scoped_source_dispatch,
        scoped_worker_launch,sealed_source_transport)
    return ParticipatingSession(modules=(kiwoom_global_lane,kiwoom_participant_session,
        current_scoped_worker_bridge,current_scoped_source_dispatch,
        scoped_worker_launch,sealed_source_transport),caller_kind='CLI')


def _mac_valuation_configuration(*,external_root,settings_env_file,base,attempt_marker):
    """No HTTP, SQL, marker or Parent: validate likely host setup failures first."""
    import os,sys
    from pathlib import Path
    from app.config import Settings
    from app.services.vnext_research_store import plain,digest
    from app.services.scoped_external_code_manifest import REQUIRED_V2,CONTRACT_V2,validate_external_manifest
    external=plain(external_root);env=plain(settings_env_file)
    if not env.is_file() or not external.is_dir():raise ValueError('mac_valuation_configuration_missing')
    settings=Settings(_env_file=env)
    credentials=dict(app_key=settings.kiwoom_app_key,secret_key=settings.kiwoom_secret_key)
    if not all(isinstance(v,str) and v.strip() for v in credentials.values()):
        raise ValueError('mac_valuation_original_credentials_missing')
    if settings.kiwoom_rest_base_url!='https://api.kiwoom.com':
        raise ValueError('mac_valuation_official_endpoint_required')
    pins={}
    for name in REQUIRED_V2:
        p=plain(external/name)
        if not p.is_file():raise ValueError('mac_valuation_external_code_missing')
        raw=p.read_bytes();pins[name]=dict(bytes=len(raw),sha256=digest(raw))
    validate_external_manifest(pins,CONTRACT_V2)
    for target in (plain(base),plain(attempt_marker)):
        if target.exists() or not target.parent.is_dir() or target.parent.stat().st_uid!=os.getuid():
            raise ValueError('mac_valuation_new_owned_scratch_required')
        s=os.statvfs(target.parent)
        if s.f_bavail*s.f_frsize<12*2**30:raise ValueError('mac_valuation_disk_guard')
    actual=Path(sys.executable).resolve(strict=True);framework=actual.parents[1]
    if (sys.platform!='darwin' or not Path('/usr/bin/sandbox-exec').is_file()
            or '/Frameworks/Python.framework/Versions/' not in str(framework)
            or not (framework/'Resources/Python.app/Contents/MacOS/Python').is_file()):
        raise ValueError('scoped_python_framework_layout_unverified')
    session=_mac_valuation_session();session.attestation();session._lane._state()
    required={'app.services.current_scoped_worker_bridge','app.services.current_scoped_source_dispatch',
        'app.services.scoped_worker_launch','app.services.sealed_source_transport'}
    if not required<={m.__name__ for m in session._modules}:
        raise ValueError('scoped_source_parent_loaded_closure_required')
    return credentials,session,pins


async def run_mac_registered_valuation(*, decision, database, preflight, base,
        external_root, settings_env_file, attempt_marker, enabled=False):
    """One trusted operator call, current four-table capture, original live lane.

    No public JSON/CLI grant or recurring approval. The exclusive marker prevents
    a second campaign after partial failure; it cannot reconstruct capabilities.
    """
    import os
    from pathlib import Path
    from app.services import prospective_class_c_owner as registration
    from app.services import registered_valuation_source_intent as intents
    from app.services.minimal_class_c_export import ExportPermission,capture_authorized_class_c
    from app.services.production_source_context import POLICY
    from app.services.vnext_research_store import digest
    import httpx
    if enabled is not True or type(decision) is not registration.ApprovalDecision:
        raise ValueError('mac_valuation_trusted_operator_explicit_enable_required')
    if (set(decision.subjects)!=set(preflight['identities']) or not 1<=len(decision.subjects)<=8
            or not decision.approved):
        raise ValueError('mac_valuation_exact_approved_subjects')
    credential_values,session,external_pins=_mac_valuation_configuration(external_root=external_root,
        settings_env_file=settings_env_file,base=base,attempt_marker=attempt_marker)
    # Static plan, host code/boot and persistent STOP checks precede any SQL.
    from app.services.valuation_research_preflight import prepare_registered_valuation
    prepared=prepare_registered_valuation(**preflight,enabled=True)
    if prepared['receipt']['planned_attempts']>19:raise ValueError('mac_valuation_budget')
    path=Path(database);s=path.stat()
    permission=ExportPermission(decision.event_id,True,path,s.st_dev,s.st_ino,decision.subjects)
    permission.require()
    marker=Path(attempt_marker)
    fd=os.open(marker,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as f:
        json.dump(dict(event=decision.event_id,approval_sha256=digest(decision.model_dump(mode='json')),
            plan_sha256=prepared['receipt']['plan_sha256'],max_HTTP=19,retries=0),f)
        f.flush();os.fsync(f.fileno())
    approval=intent=None;capture_receipt={}
    def context():
        nonlocal approval,intent
        approval=registration.record_backend_approval(decision)
        capture=capture_authorized_class_c(permission)
        from app.services.minimal_class_c_export import captured_private_snapshot
        _,r=captured_private_snapshot(capture)
        capture_receipt.update(sessions=1,SELECTs=len(r['statement_templates']),
            total_changes=r['total_changes'],cutoff=r['cutoff'],receipt_sha256=digest(r))
        intent,_=intents.issue_intent(approval=approval,capture=capture,
            generation_id=preflight['generation_id']+':intent',policy=POLICY,enabled=True)
        return dict(intent=intent,intent_generation=preflight['generation_id']+':intent',session=session)
    def credentials():
        for name,pin in external_pins.items():
            raw=(Path(external_root)/name).read_bytes()
            if pin!=dict(bytes=len(raw),sha256=digest(raw)):
                raise ValueError('mac_valuation_external_pin_changed')
        return dict(credential_values)
    try:
        async with httpx.AsyncHTTPTransport(retries=0,verify=True,trust_env=False) as inner:
            with session.operation():
                result=await run_registered_valuation_source(preflight=preflight,base=base,
                    external_root=external_root,acquire_current_context=context,
                    load_credentials=credentials,inner=inner,enabled=True)
                return dict(result,registration_capture=capture_receipt)
    except BaseException as exc:
        import re,traceback
        detail=str(exc)
        record=dict(exception_type=type(exc).__name__,detail_sha256=digest(detail.encode()),
            error_code=detail if re.fullmatch('[a-z_]{1,100}',detail) else 'DETAIL_WITHHELD',
            frames=[dict(path=f.filename,function=f.name,line=f.lineno)
                for f in traceback.extract_tb(exc.__traceback__)],
            registration_capture=capture_receipt,retry=False)
        with marker.with_suffix('.failure.json').open('x') as f:json.dump(record,f)
        raise
    finally:
        if intent is not None:intents.revoke_intent(intent)
        if approval is not None:registration.revoke_approval(approval)


def run_manual_source_canary(config, *, source_owner_factory, registry, identity, **kwargs):
    """Trusted producer -> original daily Owner -> original isolated controller.

    Factory executes only inside the admitted supervised child. It must enforce
    its separately frozen transport budget and return a live original Owner.
    This source-only entry never calls a model or fabricates an economic output.
    """
    if not callable(source_owner_factory):
        raise ValueError('backend_source_producer_required')
    from app.services.vnext_daily_research import UseRegistry
    if not isinstance(registry, UseRegistry):
        raise ValueError('live_use_registry_required_before_source')
    def operation(controller, gate):
        owner = source_owner_factory(gate)
        from app.services.vnext_incremental_ingestion import DailyDeltaOwner
        if not isinstance(owner, DailyDeltaOwner):
            raise ValueError('original_delta_and_use_owners_required')
        batch = owner.batch()
        registrations = list(batch['registrations'].values())
        if (gate['kind'] != 'EXISTING_SUBJECT_SUCCESSOR' or len(registrations) != 1
                or registrations[0]['security']['canonical_security_id'] != identity['security']
                or registrations[0]['security']['country'].lower() != gate['market']
                or any(o['payload']['calendar']['session'] != gate['session'] for o in batch['observations'])):
            raise ValueError('manual_source_owner_scope_mismatch')
        ticker = registrations[0]['security']['ticker']
        previous = [o['payload']['calendar']['session'] for o in owner.prior.batch()['observations']
                    if o['ticker'] == ticker and o['field'] in ('completed_close','ohlcv.adjusted_daily')]
        if not previous or max(previous) != gate['prior_session']:
            raise ValueError('manual_source_prior_scope_mismatch')
        result = controller.source(owner=owner, registry=registry)
        return dict(result, send=False, input_identity=identity,
                    primary_new_verified=False, source_only=True)
    return run_manual_research_canary(config, identity=identity, operation=operation, **kwargs)


def main(argv=None):
    p = argparse.ArgumentParser(description='Opt-in no-send vNext research worker')
    p.add_argument('action', choices=('health', 'schema', 'registration', 'coverage', 'sources', 'shadow', 'draft', 'valuation', 'composite', 'composite-draft', 'no-send-observe', 'valuation-source-cold'))
    p.add_argument('--source-root')
    p.add_argument('--replay-sha256')
    p.add_argument('--market', choices=('kr', 'us'))
    p.add_argument('--watermark')
    p.add_argument('--run')
    p.add_argument('--ticker')
    p.add_argument('--market-type')
    p.add_argument('--job-id')
    p.add_argument('--as-of')
    p.add_argument('--runs', nargs='+')
    p.add_argument('--historical-price', nargs=4, metavar=('ARCHIVE','ARCHIVE_SHA256','MEMBER','MEMBER_SHA256'),
                   help='Reviewed historical archive pins; reference only, no Owner issuance')
    p.add_argument('--component-reference',nargs=2,metavar=('MANIFEST','SHA256'),
                   help='Pinned original accounting replay; research only, no Owner issuance')
    args = p.parse_args(argv)
    if args.action=='valuation-source-cold':
        if not args.source_root or not args.replay_sha256:
            p.error('valuation-source-cold requires --source-root and --replay-sha256')
        print(json.dumps(cold_registered_valuation_source(args.source_root,
            expected_replay_sha256=args.replay_sha256),sort_keys=True,allow_nan=False))
        return
    if args.action == 'no-send-observe':
        if not args.market or not args.watermark:
            p.error('no-send-observe requires --market and --watermark')
        from datetime import datetime, timezone
        from app.services.vnext_no_send_controller import calendar_gate
        result = calendar_gate(args.market, datetime.now(timezone.utc), watermark=args.watermark)
        result.update(runtime='OFF_NOT_TESTED', provider_HTTP=0, model_calls=0,
                      DB_opened=False, backend_capability_required=True)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return
    if args.historical_price and args.action not in ('composite','composite-draft'):
        p.error('historical price only belongs to read-only composite')
    if args.component_reference and args.action not in ('composite','composite-draft'):
        p.error('component reference only belongs to read-only composite')
    runtime = VNextRuntime(RuntimeConfig.from_environment())
    if args.action in ('health', 'schema'):
        result = runtime.state()
    elif args.action == 'registration':
        result = runtime.registration()
    elif args.action == 'coverage':
        result = runtime.coverage()
    elif args.action == 'sources':
        result = runtime.verify_sources(args.run)
    elif args.action == 'shadow':
        result = runtime.shadow(args.run, args.ticker)
    elif args.action == 'draft':
        result = runtime.draft(args.run, args.ticker, job_id=args.job_id)
    elif args.action in ('composite', 'composite-draft'):
        if args.job_id or args.run or not args.as_of or not args.ticker:
            p.error('composite requires --ticker and --as-of; no write job or single --run')
        method = runtime.composite if args.action == 'composite' else runtime.composite_draft
        kwargs = {}
        from app.services.vnext_reference_bundle import load_family
        if args.historical_price:
            from app.services.vnext_historical_price_reference import load_pinned_archive
            kwargs['price_reference'] = load_family(load_pinned_archive, *args.historical_price)
        if args.component_reference:
            from app.services.vnext_component_reference import load_reference
            kwargs['component_reference'] = load_family(load_reference, *args.component_reference)
        result = method(args.ticker, as_of=args.as_of, run_ids=args.runs, **kwargs)
    else:
        result = runtime.valuation(args.run, args.ticker, args.market_type, job_id=args.job_id)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
