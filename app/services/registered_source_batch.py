"""Default-off batch composition of existing registration/Source/Worker Owners.

The v3 canary is unchanged. Checkpoints and historical hashes are not live
authority. Full Market, financial, technical, Native and model use stay denied.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

CONTRACT = 'registered-source-batch-v1'
ROLES = ('adjusted_daily','adjusted_weekly','adjusted_monthly','unadjusted_weekly_valuation')
GIB = 1024**3
RESPONSE = 4*1024**2
ROOT = Path(__file__).resolve().parents[2]


def require(value, reason):
    if not value:
        raise ValueError('p3_batch_'+reason)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True)
class Batch:
    batch_id: str
    security_ids: tuple[str,...]
    roles: tuple[str,...]
    sessions: tuple[tuple[str,str],...]
    expires_at: str
    maximum_http: int
    component_markets: tuple[str,...] = ()
    independent_us_closes: bool = False
    purpose: str = 'MANUAL_SHADOW_UNSENT'
    contract: str = CONTRACT
    timeout_seconds: int = 600

    @classmethod
    def parse(cls, value):
        expected = set(cls.__dataclass_fields__)
        require(set(value) == expected, 'exact_versioned_arguments')
        row = dict(value)
        for key in ('security_ids','roles','component_markets'):
            require(isinstance(row[key],list), 'sequence_type')
            row[key] = tuple(row[key])
        require(isinstance(row['sessions'],dict), 'sessions_shape')
        row['sessions'] = tuple(sorted(row['sessions'].items()))
        return cls(**row).validate()

    def validate(self):
        require(self.contract == CONTRACT and self.purpose == 'MANUAL_SHADOW_UNSENT','purpose_contract')
        require(isinstance(self.batch_id,str) and re.fullmatch(r'[A-Za-z0-9_-]{8,80}',self.batch_id),'batch_id')
        require(len(set(self.security_ids)) == len(self.security_ids) <= 22
            and all(isinstance(v,str) and v.strip()==v and v for v in self.security_ids),'security_selection')
        require(len(set(self.roles)) == len(self.roles) and set(self.roles)<=set(ROLES),'role_selection')
        require(len(set(self.component_markets)) == len(self.component_markets)
            and set(self.component_markets)<= {'kr','us'},'component_selection')
        require(bool(self.roles or self.independent_us_closes or self.component_markets),'empty_batch')
        require(not self.roles or bool(self.security_ids),'roles_need_securities')
        require(not (self.roles and self.independent_us_closes),'separate_chart_price_batches')
        require(type(self.independent_us_closes) is bool and type(self.maximum_http) is int
            and 1 <= self.maximum_http <= 64 and self.timeout_seconds == 600,'physical_caps')
        require(dict(self.sessions).keys() == {'kr','us'} and len(self.sessions)==2,'session_pair')
        for _, day in self.sessions:
            require(isinstance(day,str) and datetime.fromisoformat(day).date().isoformat()==day,'completed_session')
        expiry=datetime.fromisoformat(self.expires_at)
        require(expiry.utcoffset() is not None,'aware_expiry')
        require(len(self.security_ids)*len(self.roles)<=8,'eight_role_batch_limit')
        return self

    def public(self):
        return dict(contract=self.contract,purpose=self.purpose,batch_id=self.batch_id,
            security_ids=list(self.security_ids),roles=list(self.roles),sessions=dict(self.sessions),
            expires_at=self.expires_at,maximum_http=self.maximum_http,
            component_markets=list(self.component_markets),independent_us_closes=self.independent_us_closes,
            timeout_seconds=self.timeout_seconds)

    def require_current(self, now, sessions):
        self.validate()
        require(now.utcoffset() is not None and now < datetime.fromisoformat(self.expires_at),'expired')
        require(dict(self.sessions)==dict(sessions),'session_rolled_or_mismatch')


def admission_bytes(batch, *, retained_limit=512*1024**2):
    batch.validate()
    # Six simultaneous raw/serialized/IPC copies, eight bounded row artifacts,
    # inherited worker scratch and stream caps, retained run bytes, plus reserve.
    require(type(retained_limit) is int and 0 <= retained_limit <= 4*GIB,'retained_limit')
    peak = batch.maximum_http*RESPONSE*6 + 8*32*1024**2 + 384*1024**2 + 128*1024**2 + 16*1024**2
    return dict(response_bytes=RESPONSE,max_http=batch.maximum_http,transient_copies=6,
        expected_incremental_peak_bytes=peak,retained_limit_bytes=retained_limit,
        reserve_bytes=4*GIB,required_bytes=max(8*GIB,peak+retained_limit+4*GIB),
        scope='BATCH_ONLY_NOT_FULL_US_GUARD_REDUCTION')


def require_space(batch, paths, *, retained_limit):
    bound=admission_bytes(batch,retained_limit=retained_limit)
    rows=[]
    for value in paths:
        path=Path(value)
        require(path.is_absolute() and path.is_dir() and not any(p.is_symlink() for p in (path,*path.parents)),'writer_path')
        stat=os.statvfs(path); free=stat.f_bavail*stat.f_frsize
        require(free>=bound['required_bytes'],'writer_headroom')
        rows.append(dict(path=str(path),device=path.stat().st_dev,free_bytes=free,**bound))
    require(bool(rows),'writer_missing')
    return rows


class Budget:
    def __init__(self, maximum):
        require(type(maximum) is int and 1<=maximum<=1024,'run_budget')
        self.maximum,self.spent,self.active,self.done=maximum,0,None,{}

    def start(self, batch):
        batch.validate()
        require(self.active is None and batch.batch_id not in self.done,'duplicate_or_concurrent_batch')
        require(self.spent+batch.maximum_http<=self.maximum,'remaining_budget')
        self.active=batch

    def finish(self, actual, checkpoint):
        require(self.active is not None and type(actual) is int and 0<=actual<=self.active.maximum_http,'actual_budget')
        require(checkpoint.get('batch_id')==self.active.batch_id,'checkpoint_batch')
        self.spent+=actual
        self.done[self.active.batch_id]=dict(actual=actual,checkpoint_sha256=digest(checkpoint))
        self.active=None


def reuse_candidate(old, requested, *, live_reuse_owner=None):
    keys=('security_id','session','provider','role','adjusted','raw_sha256','receipt_sha256')
    require(set(keys)<=set(old) and set(keys)<=set(requested),'reuse_evidence_missing')
    require(all(old[k]==requested[k] for k in keys),'reuse_identity_mismatch')
    # There is no original cross-generation Source result admission in v3.
    # Caller labels, hashes and a retired capability cannot mint that authority.
    require(live_reuse_owner is None,'unrecognized_reuse_authority')
    return dict(status='MATCHED_BYTES_NOT_ADMITTED_FOR_NEW_LIVE_RUN',refetch=False,
        original_generation=old.get('generation_id'),source_owner_issued=False)


def market_status(components, original_parent=None):
    require(original_parent is None,'unrecognized_market_parent')
    return dict(components=components,parent='NOT_ISSUED',native=False,models=False)


def checked_tree(root, maximum):
    total=0
    for path in Path(root).rglob('*'):
        require(not path.is_symlink(),'output_symlink')
        if path.is_file():total+=path.stat().st_size
        require(total<=maximum,'retained_byte_cap')
    return total


def compile_batch(batch, *, bridge, frozen, stock, policy, provider_sha):
    """Only original registration projections can reach the original issuer."""
    from app.services import current_class_c_source_bridge as registration
    from app.services import current_scoped_source_owner as owner
    from app.services.scoped_source_plan import (ScopedConfig, ScopedSubject, HistoryCounts,
        ScopedCaptureSelection, ScopedCaptureSelectionV2, ScopedPriceCaptureSelection, compile_scoped_wire_contract)
    batch.validate()
    batch.require_current(datetime.now(timezone.utc), frozen['sessions'])
    documents={m:registration.memory_local_seed(bridge,frozen=frozen,plan=stock,market=m,policy=policy)
        for m in ('kr','us')}
    subjects=[];identities={}
    for market,document in documents.items():
        for row in document['roles']['security_identity']['records']:
            security=row['record'];ticker=security['ticker'];identities[ticker]=security
            subjects.append(ScopedSubject(ticker=ticker,market=market,security_id=security['canonical_security_id'],
                issuer_id=security['corp_code' if market=='kr' else 'cik'],venue=security['exchange'],
                currency='KRW' if market=='kr' else 'USD'))
    require(set(batch.security_ids)<={s.security_id for s in subjects},'unregistered_security')
    if batch.roles:
        selection=ScopedCaptureSelectionV2(contract='scoped-capture-selection-v2',
            stock_security_ids=batch.security_ids,stock_roles=batch.roles,
            market_contexts=batch.component_markets,us_completed_closes=batch.independent_us_closes)
    elif batch.independent_us_closes:
        require(not batch.component_markets,'separate_price_component_batches')
        require(all(s.market=='us' for s in subjects if s.security_id in batch.security_ids),'US_independent_price_only')
        selection=ScopedPriceCaptureSelection(contract='scoped-price-capture-selection-v1',close_security_ids=batch.security_ids)
    else:
        selection=ScopedCaptureSelection(stock_markets=(),stock_roles=(),market_contexts=batch.component_markets,
            us_completed_closes=False)
    history={market:HistoryCounts(**{r.role:r.count for r in stock.reads if r.market==market}) for market in ('kr','us')}
    config=ScopedConfig(subjects=tuple(sorted(subjects,key=lambda s:s.security_id)),
        kr_history=history['kr'],us_history=history['us'],kr_max_pages=20,capture_selection=selection)
    wire=compile_scoped_wire_contract(config=config,identities=identities,generation_id=stock.run_id,
        at=stock.frozen_at,code_sha=stock.implementation_sha,provider_config_sha256=provider_sha,retries=0)
    require(sum(d.max_transport_attempts for d in wire['request_plan'].descriptors)<=batch.maximum_http,'compiled_calls_exceed_batch')
    spec=owner.ScopedSourceSpec(config=config,generation_id=stock.run_id,cutoff=stock.frozen_at,
        code_sha=stock.implementation_sha,provider_config_sha256=provider_sha,maximum_attempts=batch.maximum_http)
    parent=owner.issue_parent(registration_owners=registration.memory_owners(bridge),admitted_projections=documents,
        spec=spec,plan=wire['request_plan'],policy=policy,code_pins=owner.current_code_pins(),enabled=True)
    stock_wire=dict(contract='current-scoped-stock-capture-v1',run_id=stock.run_id,
        acquisition_id=stock.acquisition_id+'-batch',frozen_at=stock.frozen_at.isoformat(),
        reads=[r.model_dump(mode='json') for r in wire['stock_reads']],owner_files=json.loads(wire['owner_files_json']))
    return parent,wire,stock_wire


async def execute_chart_batch(*, batch, parent, wire, stock, manifest, configuration, settings, session, output):
    """Original constructors/commands/role issuer, never a replacement collector."""
    import asyncio
    import httpx
    from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
    from app.services.current_scoped_worker_bridge import ScopedBridge
    from app.services.sealed_source_transport import SealedSourceTransport
    from app.services.scoped_worker_launch import CUSTODY_POLICY
    from app.services import current_scoped_source_results as results
    from app.services import current_scoped_source_owner as owner
    from app.services.official_registered_source_runtime import original_external_pins
    from app.services.unified_run_artifacts import durable_json
    from app.services.kiwoom_participant_session import ParticipatingSession
    require(type(session) is ParticipatingSession,'original_session')
    session.attestation()
    require(batch.roles and not batch.component_markets and not batch.independent_us_closes,'chart_executor_scope')
    require(settings.kiwoom_rest_base_url.rstrip('/')=='https://api.kiwoom.com','original_provider_origin')
    require(Path(output).is_absolute() and not Path(output).exists(),'fresh_batch_output')
    output=Path(output);output.mkdir(mode=0o700)
    worker_output=output/'worker';worker_output.mkdir(mode=0o700)
    credentials=dict(app_key=settings.kiwoom_app_key,secret_key=settings.kiwoom_secret_key)
    require(all(isinstance(v,str) and v for v in credentials.values()),'credentials_required')
    plan=wire['request_plan']
    dispatcher=CurrentScopedDispatcher(parent=parent,plan=plan,root=output/'dispatch',
        owners={d.normalizer:d.owner_sha256 for d in plan.descriptors},
        config_identities={'kiwoom':next(d.config_identity_sha256 for d in plan.descriptors)},
        credential_presence={'kiwoom':True},secrets=tuple(credentials.values()),account_pacer=session._lane)
    require(dispatcher._account_pacer is session._lane,'single_original_lane')
    pins=original_external_pins(manifest,configuration['external_code_contract'])
    external=Path(configuration['external_root'])
    for name,expected in pins.items():
        path=external/name
        require(not any(p.is_symlink() for p in (path,*path.parents)),'external_path')
        raw=path.read_bytes()
        require(dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())==expected,'external_code_changed')
    envelope=dict(stage=str(ROOT),output=str(worker_output),external_root=str(external),external_pins=pins,
        external_code_contract=configuration['external_code_contract'],stock_plan=stock,
        request_interval=max(1.5,settings.kiwoom_rest_request_interval_seconds),
        latest_completed_us_session=dict(batch.sessions)['us'],us_market_symbols=[],
        read_paths=[str(ROOT/name) for name in manifest['source_pins']]+[str(external/name) for name in pins])
    frozen=output/'worker-plan.json';durable_json(frozen,envelope,exclusive=True)
    worker=ScopedBridge(parent=parent,original_plan=plan,
        transport=SealedSourceTransport(dispatcher,httpx.AsyncHTTPTransport(retries=0),providers={'kiwoom'}),
        worker=ROOT/'scripts/current_scoped_source_worker.py',frozen=frozen,
        sha=hashlib.sha256(frozen.read_bytes()).hexdigest(),output=worker_output,
        credentials=credentials,market_reads=(),source_session=session,custody_policy=CUSTODY_POLICY)
    receipts=[];artifacts=[];gaps=[]
    try:
        results.bind_capture(parent,wire,stock,dispatcher,dispatcher.root,worker_output,worker)
        async def capture():
            first=await worker.command({'stocks':True})
            require(first.get('status')=='CAPTURE_COMPLETE_NOT_QUALIFIED','capture_failed')
            for number in (1,2):
                replay=await worker.command({'replay':number})
                require(replay.get('status')=='REPLAY_RESULT','original_replay_missing')
                checked_tree(output,512*1024**2)
            for read in wire['stock_reads']:
                if read.timeframe=='daily':await worker.command({'projection':read.entry_id})
            await worker.shutdown()
        await asyncio.wait_for(capture(),timeout=batch.timeout_seconds)
        require(worker.process is not None and worker.process.returncode==0,'worker_not_normal_end')
        for read in wire['stock_reads']:
            cap=None
            try:
                cap=results.issue_source_result(parent,dispatcher=dispatcher,entry_id=read.entry_id)
                value=results.read_source_rows(parent,cap,dispatcher=dispatcher,entry_id=read.entry_id)
                receipts.append(value['receipt'])
                path=dispatcher.root/'issued-source'/f'{len(receipts):02d}.json'
                durable_json(path,value['rows'],exclusive=True)
                artifacts.append(dict(entry_id=read.entry_id,path=str(path.relative_to(dispatcher.root)),
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            except (ValueError,KeyError,TypeError,OSError) as exc:
                gaps.append(dict(entry_id=read.entry_id,status='ORIGINAL_OWNER_REJECTED',
                    error_type=type(exc).__name__,error_sha256=hashlib.sha256(str(exc).encode()).hexdigest()))
            finally:
                if cap is not None:results.revoke_source_result(cap)
        checked_tree(output,512*1024**2)
        return dict(batch_id=batch.batch_id,status='SOURCE_ISSUED_COLD_REQUIRED' if receipts else 'ORIGINAL_OWNER_REJECTED_ALL',
            receipts=receipts,row_artifacts=artifacts,gaps=gaps,physical_HTTP=dispatcher.physical_attempts,
            capture=str(dispatcher.root),plan=dispatcher.plan.model_dump(mode='json'),
            physical_receipts={key:value['receipt_sha256'] for key,value in dispatcher.results.items() if value['status']=='PASS'},
            models=0,native=False,Market=market_status('NOT_REQUESTED'))
    finally:
        try:await worker.shutdown()
        finally:
            try:await worker.transport.inner.aclose()
            finally:
                durable_json(output/'batch-runtime-end.json',dict(batch_id=batch.batch_id,
                    physical_HTTP=dispatcher.physical_attempts,halted=dispatcher.halted,
                    worker_pid=worker.process.pid if worker.process else None,
                    worker_exit=worker.process.returncode if worker.process else None,
                    roles_issued=len(receipts),gaps=gaps),exclusive=True)
                owner.revoke_parent(parent)


def validate_cold_roles(data, read_rows, *, wm_context=None):
    """Byte readback only; no capability creation or current-use promotion."""
    require(isinstance(data,dict) and {'batch','contract','batch_id','batch_sha256',
        'expected_reads','receipts','artifacts','plan'} <= data.keys(),'cold_required_fields')
    receipt_fields={'entry_id','receipt_sha256','security_id','target_session','generation_id',
        'plan_sha256','parent_receipt_sha256','consumer','allowed_use','normalized_sha256',
        'rows','requested_rows','technical_signal','completed_price_authority','financial_use',
        'valuation_use','economic_use','D01_D02','native_use','full22_native','model_use'}
    require(all(isinstance(data[k],list) for k in ('expected_reads','receipts','artifacts'))
        and isinstance(data['plan'],dict)
        and {'generation_id','parent_receipt_sha256'} <= data['plan'].keys()
        and all(isinstance(r,dict) and receipt_fields <= r.keys() for r in data['receipts'])
        and all(isinstance(r,dict) and {'entry_id','sha256'} <= r.keys() for r in data['artifacts'])
        and all(isinstance(r,dict) and {'entry_id','role','canonical_security_id',
            'latest_completed_session','market','count'} <= r.keys() for r in data['expected_reads']),
        'cold_required_fields')
    batch=Batch.parse(data['batch'])
    require(data['contract']=='registered-source-batch-cold-v1' and data['batch_id']==batch.batch_id,'cold_batch')
    require(data['batch_sha256']==digest(batch.public()),'cold_batch_digest')
    entries={r['entry_id']:r for r in data['expected_reads']}
    require(bool(data['receipts']) and len(entries)==len(data['expected_reads']),'cold_expected_roles')
    require(len(data['receipts'])==len(data['artifacts']),'cold_artifact_count')
    seen=set(); accepted=[]
    for receipt,artifact in zip(data['receipts'],data['artifacts'],strict=True):
        entry=receipt['entry_id']; core=dict(receipt); receipt_sha=core.pop('receipt_sha256')
        require(entry in entries and entry not in seen and artifact['entry_id']==entry,'cold_role_binding')
        read=entries[entry]
        require(read['role'] in batch.roles and read['canonical_security_id'] in batch.security_ids
            and receipt['security_id']==read['canonical_security_id']
            and receipt['target_session']==read['latest_completed_session']==dict(batch.sessions)[read['market']],'cold_frozen_selection')
        require(digest(core)==receipt_sha and receipt['generation_id']==data['plan']['generation_id']
            and receipt['plan_sha256']==digest(data['plan'])
            and receipt['parent_receipt_sha256']==data['plan']['parent_receipt_sha256'],'cold_receipt_binding')
        require(receipt['consumer']=='SCOPED_SOURCE_ONLY' and receipt['allowed_use']=='BOUND_SOURCE_ROWS_ONLY'
            and all(receipt[k] is False for k in ('technical_signal','completed_price_authority','financial_use',
                'valuation_use','economic_use','D01_D02','native_use','full22_native','model_use')),'cold_scope')
        raw,rows=read_rows(artifact)
        require(hashlib.sha256(raw).hexdigest()==artifact['sha256']
            and digest(rows)==receipt['normalized_sha256']
            and len(rows)==receipt['rows']==receipt['requested_rows']==read['count'],'cold_rows')
        period=None
        if receipt.get('contract') == 'current-scoped-monitoring-role-source-receipt-v1':
            from app.services.query_time_monitoring_price import validate_monitoring_readback
            from app.services.scoped_source_plan import ScopedStockRead
            value=receipt['monitoring_snapshot'];observation=value['observation']
            require(receipt['current_source_authority'] is False and value['window_eligible'] is True,
                'cold_monitoring_scope')
            period=validate_monitoring_readback(value,rows=rows,read=ScopedStockRead.model_validate(read),
                frozen_at=datetime.fromisoformat(observation['frozen_at']),
                observed_at=datetime.fromisoformat(observation['observed_at']),source_pages=observation['source_pages'])
        elif receipt.get('contract') in ('current-scoped-role-source-receipt-v2-wm','pending-scoped-role-source-receipt-v1-wm'):
            from app.services.wm_period_currentness import validate_period_readback
            from app.services.scoped_source_plan import ScopedStockRead
            require(wm_context is not None,'cold_wm_context_required')
            period=validate_period_readback(receipt,read=ScopedStockRead.model_validate(read),rows=rows,**wm_context)
        else:
            require('period_proof' not in receipt and 'period_evidence' not in receipt,'cold_wm_version_alias')
        seen.add(entry);accepted.append(dict(entry_id=entry,rows=len(rows),**({'period':period} if period else {})))
    return dict(status='BATCH_SEALED_BYTES_COLD_PASS_NOT_OWNER_REISSUANCE',roles=accepted,new_live_authority=False)
