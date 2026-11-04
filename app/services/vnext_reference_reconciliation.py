"""Append/cold-read original-owner research references, not current qualification."""
from copy import deepcopy
import json
import os
from app.services.vnext_kis_source_state import ReviewedKISSourceObservations,SourceState
from app.services.vnext_reported_observations import historical_kis_reference
from app.services.vnext_research_ingestion import AppendResearchStore,current_identity,bind_current_identity,_append
from app.services.vnext_research_store import digest,encoded,plain

CONTRACT='original-owner-reference-reconciliation-v1'

class ReconciledReferences:
    def __init__(self, source_owner, historical_owner):
        if not isinstance(source_owner,ReviewedKISSourceObservations) or not callable(historical_owner):
            raise ValueError('original_owner_capabilities_required')
        self.source,self.history=source_owner,historical_owner
        self.revoked=False

    def revoke(self):self.revoked=True

    def project(self,security,cutoff,*,include_history):
        if self.revoked:raise ValueError('reference_owner_revoked')
        state=self.source.project(security=security,as_of=cutoff)
        if state is None:raise ValueError('original_security_missing')
        history=historical_kis_reference(self.history,security=security,as_of=cutoff) if include_history else None
        records=[]
        if history and history['facts']:
            records.append(dict(kind='HISTORICAL_REFERENCE',original=history,
                fields=[dict(field='historical.'+f['metric'],value=f) for f in history['facts']]))
        if state['retrieval_state']==SourceState.EMPTY.value:
            records.append(dict(kind='SOURCE_AVAILABILITY',original=state,
                fields=[dict(field='source.KIS_NORMAL_EMPTY',value=state)]))
        return dict(contract=CONTRACT,security=deepcopy(security),cutoff=cutoff,records=records,
            strict_native=False,direction=False,current_qualification=False)

def _rows(projection,run_id):
    for rec in projection['records']:
        body=encoded(dict(contract=CONTRACT,security=projection['security'],kind=rec['kind'],
            original=rec['original'],derived_owner_replay=True,not_new_HTTP=True))
        sha=digest(body);key=digest([CONTRACT,projection['security']['canonical_security_id'],rec['kind'],sha])
        capid=digest([run_id,'OriginalOwnerReplay',key])
        obs=[]
        for f in rec['fields']:
            payload=dict(contract=CONTRACT,kind=rec['kind'],value=f['value'],owner_projection_sha256=digest(projection),
                original_source_generation=rec['original']['source_generation'],strict_native=False,direction=False,current_qualification=False)
            obs.append((digest([run_id,projection['security']['ticker'],f['field'],sha]),run_id,
                projection['security']['ticker'],f['field'],rec['kind'],sha,encoded(payload).decode()))
        yield body,sha,key,capid,obs

def ingest(config,*,owner,requests,run_id,job_id,cutoff,replayed_at):
    if not isinstance(owner,ReconciledReferences):raise ValueError('live_reference_owner_required')
    from app.services.vnext_composite_research import instant
    if instant(replayed_at)<instant(cutoff):raise ValueError('replay_time_before_data_cutoff')
    store=AppendResearchStore(config)
    initial=[owner.project(q['security'],cutoff,include_history=q['include_history']) for q in requests]
    intent=dict(contract=CONTRACT,requests=requests,projections=initial,run_id=run_id,cutoff=cutoff,replayed_at=replayed_at)
    with store.atomic_job(job_id,intent) as cell:
        observations=[];captures=[]
        with store.connect() as c:
            _append(c,'research_run',('run_id','started_at','as_of','status'),
                (run_id,replayed_at,cutoff,'DERIVED_HISTORICAL_REFERENCE_NOT_NEW_CAPTURE'),already_committed=bool(cell['previous']))
            for q,p in zip(requests,initial):
                registration=current_identity(store,q['security']['ticker'])
                bind_current_identity(q['security'],registration,expected_version=q['registration_version'])
                if owner.project(q['security'],cutoff,include_history=q['include_history'])!=p:raise ValueError('owner_changed')
                for body,sha,key,capid,rows in _rows(p,run_id):
                    path=plain(store.path.parent/'raw'/sha);path.parent.mkdir(exist_ok=True,mode=0o700)
                    if not path.exists():
                        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
                        with os.fdopen(fd,'wb') as f:f.write(body);f.flush();os.fsync(f.fileno())
                    if not path.is_file() or path.stat().st_nlink!=1 or path.read_bytes()!=body:raise ValueError('replay_CAS_mismatch')
                    receipt=dict(contract=CONTRACT,raw_sha256=sha,run_id=run_id,replayed_at=replayed_at,data_cutoff=cutoff,
                        derived_owner_replay=True,new_HTTP=False,original_dates_unchanged=True)
                    _append(c,'source_capture',('capture_id','run_id','provider','request_key','raw_sha','raw_path','captured_at','receipt_json'),
                        (capid,run_id,'OriginalOwnerReplay',key,sha,str(path),replayed_at,encoded(receipt).decode()),already_committed=bool(cell['previous']))
                    captures.append(capid)
                    for row in rows:
                        _append(c,'research_observation',('observation_id','run_id','ticker','field','status','source_sha','payload_json'),row,already_committed=bool(cell['previous']))
                        observations.append(row[0])
        result=dict(contract=CONTRACT,run_id=run_id,observations=observations,captures=captures,
            projections_sha256=digest(initial),strict_native=False,new_HTTP=0)
        if cell['previous'] and cell['previous']['result']!=result:raise ValueError('committed_reference_drift')
        cell['result']=result
    return result

def cold_read(config,*,owner,requests,run_id,job_id,cutoff,replayed_at):
    if not isinstance(owner,ReconciledReferences):raise ValueError('live_reference_owner_required')
    store=AppendResearchStore(config);out=[]
    expected=[owner.project(q['security'],cutoff,include_history=q['include_history']) for q in requests]
    intent=dict(contract=CONTRACT,requests=requests,projections=expected,run_id=run_id,cutoff=cutoff,replayed_at=replayed_at)
    from app.services.vnext_runtime import CONTRACT as runtime_contract
    with store.connect() as c:
        journal=c.execute('select value from research_meta where key=?',(runtime_contract+':job:'+job_id,)).fetchone()
        if journal is None:raise ValueError('missing_committed_reference_job')
        journal=json.loads(journal[0])
        if journal['status']!='COMMITTED' or journal['request_sha256']!=digest(intent):raise ValueError('committed_reference_request_mismatch')
        for q in requests:
            bind_current_identity(q['security'],current_identity(store,q['security']['ticker']),expected_version=q['registration_version'])
            p=owner.project(q['security'],cutoff,include_history=q['include_history'])
            for body,sha,key,capid,rows in _rows(p,run_id):
                cap=c.execute('select raw_sha,raw_path from source_capture where capture_id=?',(capid,)).fetchone()
                expected=plain(store.path.parent/'raw'/sha)
                if cap!=(sha,str(expected)) or expected.stat().st_nlink!=1 or expected.read_bytes()!=body:raise ValueError('cold_reference_capture_mismatch')
                for row in rows:
                    actual=c.execute('select observation_id,run_id,ticker,field,status,source_sha,payload_json from research_observation where observation_id=?',(row[0],)).fetchone()
                    if actual!=row:raise ValueError('cold_reference_observation_mismatch')
            out.append(p)
    return out
