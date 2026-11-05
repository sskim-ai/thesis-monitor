"""Original Market collectors with version-preserving private evidence handoff.

No registration, Provider entitlement, Full Market Parent or investment rights.
"""
from dataclasses import asdict
from datetime import date
import hashlib,json
from pathlib import Path
from types import SimpleNamespace
import httpx
from app.macro.providers.base import CollectedObservation
from app.macro.providers.market import normalize_market_observation
from app.services.current_scoped_source_dispatch import CurrentScopedRequestPlan
from app.services.scoped_source_plan import ScopedMarketComponentConfig
from app.services.unified_snapshot_contract import digest,encoded

CONTRACT='original-market-component-cold-bundle-v1'

async def execute_capture(*,market,config,worker,run,wire,base,credentials,windows,checkpoint):
    """One collector lifetime, two full Worker replays, original component Owner."""
    import asyncio
    from app.services.market_component_handoff import bind_original_component,read_source_component
    try:
        collection=await collect_original(market=market,worker=worker,run=run,wire=wire,base=base,
            credentials=credentials,checkpoint=checkpoint)
        await drain_selected_market_slots(worker,run)
        for n in (1,2):
            result=await worker.command({'market_replay':n})
            if result.get('status')!='MARKET_COMPONENT_RAW_REPLAY_PASS' or result['components']<1:
                raise ValueError('market_full_original_worker_replay_denied')
        record=windows.finish()
    finally:
        await worker.shutdown();await worker.transport.shutdown()
    handle,receipt=await asyncio.to_thread(bind_original_component,dispatcher=run,market=market,
        worker_bridge=worker,enabled=True)
    proof=read_source_component(handle)
    bundle=component_bundle(market=market,config=config,run=run,worker=worker,windows=record,owner_proof=proof)
    return dict(collection=collection,owner_receipt=receipt,bundle=bundle)

async def drain_selected_market_slots(worker,run):
    """Finish only response-selected slots in the original frozen Market plan.

    The original count-limited Market consumer can stop with enough bars while
    its original Source plan still selects a bounded continuation page.
    """
    from app.services.sealed_response_binding import SlotNotSelected
    for descriptor in run.plan.descriptors:
        key=descriptor.logical_request_id
        if key in run.used:continue
        if not key.startswith(('kr_market:','us_market:')):
            raise ValueError('market_unconsumed_non_market_slot')
        try:wire,_,_=run.resolve(key)
        except SlotNotSelected:continue
        reply=await worker.command({'market_wire':dict(logical_id=key,request_json=wire)})
        if reply.get('status')!=200:raise ValueError('market_selected_continuation_rejected')

def verified_raw_hashes(value,plan,root):
    """NOT_SELECTED is a bound no-I/O decision, never a response with raw bytes."""
    from app.services.sealed_fresh_dispatch import _binding_parent
    from app.services.sealed_response_binding import resolve_response_binding,SlotNotSelected
    descriptors={d.logical_request_id:d for d in plan.descriptors}
    if set(value)!=set(descriptors):raise ValueError('market_full_plan_result_set')
    hashes=set()
    for key,row in value.items():
        if row.get('status')=='PASS':hashes.add(row['raw_sha256']);continue
        d=descriptors[key];actual=json.loads((root/'receipts'/key/'final.json').read_bytes())
        identity=dict(generation_id=plan.generation_id,logical_request_id=key,descriptor_sha256=d.descriptor_sha256,
            request_sha256=d.request_semantic_sha256,plan_sha256=plan.plan_sha256,role=d.consumer_role)
        if (row!=actual or row.get('status')!='NOT_SELECTED' or row.get('attempts')!=[]
                or digest({k:v for k,v in row.items() if k!='receipt_sha256'})!=row['receipt_sha256']
                or any(row.get(k)!=v for k,v in identity.items()) or d.response_binding is None
                or set(row['parent_receipts'])!=set(d.response_binding.parents)):
            raise ValueError('market_unselected_original_receipt_required')
        parents={k:_binding_parent(root,plan,k,s) for k,s in row['parent_receipts'].items()}
        try:resolve_response_binding(d.request_json,d.response_binding,parents)
        except SlotNotSelected as exc:
            if str(exc)!=row['reason']:raise ValueError('market_unselected_reason_mismatch')
        else:raise ValueError('market_selected_slot_cannot_be_skipped')
    return hashes

def normalize_observation(value):
    if type(value) is not CollectedObservation:
        raise ValueError('market_original_dataclass_required')
    result=asdict(value);result['observed_at']=value.observed_at.isoformat()
    return result

def preserve_plan(plan):
    if type(plan) is not CurrentScopedRequestPlan:
        raise ValueError('market_current_scoped_plan_type_required')
    value=plan.model_dump(mode='json')
    rebuilt=CurrentScopedRequestPlan.model_validate(value)
    if rebuilt!=plan or rebuilt.plan_sha256!=plan.plan_sha256:
        raise ValueError('market_current_scoped_plan_roundtrip')
    return value

def prepare_capture(*,parent,wire,session,base,credentials,inner,external_root):
    """Freeze the original launch closure and exact Worker/transport objects."""
    import ast
    from app.services import pending_source_parent as pending
    from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
    from app.services.sealed_source_transport import SealedSourceTransport
    from app.services.current_scoped_worker_bridge import ScopedBridge
    from app.services.scoped_worker_launch import CUSTODY_POLICY
    from app.services.scoped_external_code_manifest import REQUIRED_V2,CONTRACT_V2
    from app.services.same_session_market_windows import SameSessionWindows
    root=Path(__file__).resolve().parents[2];base=Path(base);external=Path(external_root)
    if base.exists() or base.is_symlink():raise ValueError('market_new_private_capture_root_required')
    base.mkdir(mode=0o700,parents=True);out=base/'worker';out.mkdir(mode=0o700)
    plan=wire['request_plan']
    run=CurrentScopedDispatcher(parent=parent,plan=plan,root=base/'dispatch',
        owners={d.normalizer:d.owner_sha256 for d in plan.descriptors},
        config_identities={'kiwoom':plan.descriptors[0].config_identity_sha256},
        credential_presence={'kiwoom':True},secrets=tuple(credentials.values()),account_pacer=session._lane)
    transport=SealedSourceTransport(run,inner,providers={'kiwoom'});windows=SameSessionWindows(transport)
    pins={}
    for n in REQUIRED_V2:
        p=external/n
        if p.is_symlink():raise ValueError('market_external_code_symlink')
        raw=p.read_bytes();pins[n]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    todo=['scripts/current_scoped_source_worker.py'];seen=set()
    while todo:
        n=todo.pop()
        if n in seen:continue
        p=root/n;seen.add(n);parts=Path(n).parts
        for depth in range(1,len(parts)):
            init='/'.join(parts[:depth])+'/__init__.py'
            if (root/init).is_file() and init not in seen:todo.append(init)
        for node in ast.walk(ast.parse(p.read_bytes())):
            if isinstance(node,ast.Import):names=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom) and node.module:
                module=node.module if not node.level else '.'.join(parts[:-node.level])+'.'+node.module
                names=[module]+[module+'.'+a.name for a in node.names]
            else:continue
            for module in names:
                if module.startswith(('app.','scripts.')):
                    for c in (module.replace('.','/')+'.py',module.replace('.','/')+'/__init__.py'):
                        if (root/c).is_file() and c not in seen:todo.append(c)
    stock=dict(contract='current-scoped-stock-capture-v1',run_id=plan.generation_id,
        acquisition_id=plan.generation_id,frozen_at=plan.frozen_at.isoformat(),reads=[],
        owner_files=json.loads(wire['owner_files_json']))
    frozen=base/'frozen.json'
    envelope=dict(stage=str(root),output=str(out),external_root=str(external),external_pins=pins,
        external_code_contract=CONTRACT_V2,stock_plan=stock,request_interval=1.5,
        latest_completed_us_session=str(next(p.target for p in wire['sessions'] if p.market=='us')),
        us_market_symbols=list(wire['us_market_symbols']),pending_handoff=pending.public_handoff(parent),
        market_wire_templates={d.logical_request_id:d.model_dump(mode='json') for d in plan.descriptors},
        read_paths=[str(root/n) for n in sorted(seen)]+[str(external/n) for n in sorted(pins)])
    with frozen.open('xb') as f:f.write(encoded(envelope))
    worker=ScopedBridge(parent=parent,original_plan=plan,transport=transport,physical_windows=windows,
        worker=root/'scripts/current_scoped_source_worker.py',frozen=frozen,
        sha=hashlib.sha256(frozen.read_bytes()).hexdigest(),output=out,credentials=dict(credentials),
        market_reads=[],source_session=session,custody_policy=CUSTODY_POLICY)
    return run,transport,worker,windows

def sealed_checkpoint(run):
    from app.services.sealed_fresh_dispatch import consume_bound_result
    plan=preserve_plan(run.plan)
    for key,row in run.results.items():
        consume_bound_result(root=run.root,plan=run.plan,logical_id=key,receipt_sha256=row['receipt_sha256'])
    return dict(contract='market-original-inflight-checkpoint-v1',plan=plan,
        plan_sha256=run.plan.plan_sha256,generation_id=run.plan.generation_id,
        sealed_receipts={k:r['receipt_sha256'] for k,r in run.results.items()},physical=run.physical_attempts,
        completed=False,MarketParent=False)

async def collect_original(*,market,worker,run,wire,base,credentials,checkpoint):
    """Checkpoint once inside the original full-plan/token lifetime."""
    from app.services.unified_source_policy import UnifiedSourcePolicy
    session=next(p.target for p in wire['sessions'] if p.market==market)
    if market=='kr':
        from app.providers.kiwoom_rest_client import KiwoomRestClient
        from app.services.kiwoom_kr_market_context_service import KiwoomKrMarketContextService
        from app.services.unified_kiwoom_observer import KiwoomRead,KiwoomReceiptObserver
        from app.services.market_worker_rpc import MarketWorkerRPC
        class CheckpointRPC(MarketWorkerRPC):
            checked=False
            async def handle_async_request(self,request):
                response=await super().handle_async_request(request)
                if request.url.path!='/oauth2/token' and not self.checked:
                    self.checked=True;await checkpoint()
                return response
        reads=tuple(KiwoomRead.model_validate(x) for x in json.loads(wire['kr_market_reads_json']))
        observer=KiwoomReceiptObserver(root=base/'kr-market',run_id=run.plan.generation_id,
            attempt_id=run.plan.generation_id,session_date=session,reads=reads,
            policy=UnifiedSourcePolicy(frozenset({'kiwoom_rest'})),completed_session_only=True)
        client=KiwoomRestClient(**credentials,base_url='https://api.kiwoom.com',timeout_seconds=60,
            request_interval_seconds=1.5,max_retries=0,transport=CheckpointRPC(worker),source_observer=observer)
        collection=await KiwoomKrMarketContextService(client,max_pages=20,completed_session_only=True).collect(
            session_date=session,observed_at=run.plan.frozen_at)
        return dict(contract='ORIGINAL_KR_COLLECTOR_COMPLETE',reads=len(reads),
            audit=collection.audit.model_dump(mode='json'))
    if market!='us':raise ValueError('market_original_market_required')
    from app.services.unified_source_observer import OhlcvRead,OhlcvReceiptObserver
    reads=tuple(OhlcvRead(role='us_market:'+symbol,symbol=symbol,market='us',provider='ohlcv_analyst',
        response_provider='kiwoom',period='daily',adjusted=True,session_date=session,max_requests=1,
        params=dict(symbol=symbol,market='US',periods='daily',count=2,include_indicators='false',indicator_limit=0,adjusted='true'))
        for symbol in wire['us_market_symbols'])
    worker.market_reads=reads
    observer=OhlcvReceiptObserver(root=base/'us-market',run_id=run.plan.generation_id,attempt_id=run.plan.generation_id,
        reads=reads,policy=UnifiedSourcePolicy(frozenset({'ohlcv_analyst','kiwoom'})))
    reply=await worker.command({'discovery':True})
    if reply.get('status')!='DISCOVERY_CAPTURE_COMPLETE_NOT_QUALIFIED':
        raise ValueError('market_original_discovery_rejected')
    async with httpx.AsyncClient(transport=worker,base_url='http://scoped-source.local') as client:
        for index,read in enumerate(reads):
            response=await observer.get(client,'/ohlcv',params=read.params)
            response.raise_for_status()
            observation=normalize_market_observation(response.json(),symbol=read.symbol,source_url='http://scoped-source.local/ohlcv')
            if observation is None:raise ValueError('market_original_observation_missing')
            observer.normalized(response,normalized=normalize_observation(observation),contract='market-observation-v1',
                valid=True,fingerprint=hashlib.sha256(Path(normalize_market_observation.__code__.co_filename).read_bytes()).hexdigest())
            if index==0:await checkpoint()
    return dict(contract='ORIGINAL_US_COLLECTOR_COMPLETE',reads=len(reads))

def component_bundle(*,market,config,run,worker,windows,owner_proof):
    plan=preserve_plan(run.plan)
    if (market not in ('kr','us') or config.capture_selection.market_contexts!=(market,)
            or worker.process is None or worker.process.returncode!=0):
        raise ValueError('market_component_exact_scope_closed_worker_required')
    return dict(contract=CONTRACT,market=market,config=config.model_dump(mode='json'),plan=plan,
        cutoff=run.plan.frozen_at.isoformat(),root=str(run.root),worker=str(worker.output),
        results=run.results,commands=worker.commands,windows=windows,owner_proof=owner_proof,
        full_market_parent=False)

def cold_component(value):
    """Independent original normalized/aggregate replay, no live grant recreation."""
    from datetime import datetime
    from app.services.same_session_market_windows import cold_window_readback
    from app.services.current_scoped_source_results import _market
    from app.services.unified_snapshot_contract import digest
    if value.get('contract')!=CONTRACT or value.get('full_market_parent') is not False:
        raise ValueError('market_component_bundle_contract')
    plan=CurrentScopedRequestPlan.model_validate(value['plan'])
    config=ScopedMarketComponentConfig.model_validate(value['config']);market=value['market']
    if (config.capture_selection.market_contexts!=(market,) or value['cutoff']!=plan.frozen_at.isoformat()
            or any(d.market not in (market,'global') for d in plan.descriptors)):
        raise ValueError('market_component_date_or_market_mismatch')
    root=Path(value['root']);worker=Path(value['worker'])
    raw_hashes=verified_raw_hashes(value['results'],plan,root)
    for n in (1,2):
        artifact=worker/f'market-replay-{n}.json'
        rows=json.loads(artifact.read_bytes())
        if not rows:raise ValueError('market_component_empty_worker_replay')
        for row in rows:
            path=worker/row['artifact']
            if path.is_symlink() or path.parent!=worker or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:
                raise ValueError('market_component_worker_raw_hash')
            if row['sha256'] not in raw_hashes:
                raise ValueError('market_component_worker_raw_not_sealed')
        command={'market_replay':n}
        proof=dict(status='MARKET_COMPONENT_RAW_REPLAY_PASS',artifact=artifact.name,
            sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),components=len(rows))
        if len([r for r in value['commands'] if r['command']==command and r['result_sha256']==digest(proof)])!=1:
            raise ValueError('market_component_worker_replay_command_binding')
    window_cold=cold_window_readback(plan=plan,root=root,record=value['windows'])
    dispatcher=SimpleNamespace(root=root,results=value['results'])
    spec=SimpleNamespace(config=config,cutoff=plan.frozen_at)
    actual=_market(market,spec,plan,dispatcher,root,value['commands'] if market=='us' else None,
        qualification_cutoff=datetime.fromisoformat(value['owner_proof']['qualification_cutoff']))
    if actual!=value['owner_proof']:raise ValueError('market_component_original_owner_changed')
    return dict(status='ORIGINAL_COMPONENT_OWNER_COLD_PASS_NOT_FULL_PARENT',market=market,
        generation_id=plan.generation_id,component_sha256=actual['component_sha256'],window_cold=window_cold,
        MarketParent=False,native_use=False)
