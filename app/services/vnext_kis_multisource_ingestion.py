"""Append-only derivative custody; original parents keep their real generations."""
import json
import os
from app.services.vnext_research_store import digest,encoded,plain
from app.services.vnext_research_ingestion import AppendResearchStore,current_identity,bind_current_identity,_append
from app.services.vnext_kis_source_ingestion import _capture
from app.services.vnext_kis_multisource import ReviewedMultisourceKIS,CONTRACT
from app.services.vnext_runtime import ID


def source_custody(store,owner,security):
    b=owner.original_batch()['source']
    item=next(x for x in b['captures'] if x['security']['ticker']==security['ticker'])
    ident,key,receipt=_capture(item,b);sha=digest(item['raw'].encode())
    path=plain(store.path.parent/'raw'/sha)
    with store.connect() as c:
        row=c.execute('SELECT capture_id,run_id,provider,request_key,raw_sha,raw_path,captured_at,receipt_json FROM source_capture WHERE capture_id=?',(ident,)).fetchone()
    expected=(ident,b['plan']['generation_id'],'KIS',key,sha,str(path),receipt['captured_at'],encoded(receipt).decode())
    if row!=expected or not path.is_file() or path.stat().st_nlink!=1 or path.read_bytes()!=item['raw'].encode():
        raise ValueError('original_stored_source_custody_required')
    return ident


def ingest(config,*,owner,job_id,run_id,registration_versions,cutoff,metrics=None):
    if not isinstance(owner,ReviewedMultisourceKIS):
        raise ValueError('trusted_multisource_capability_required')
    if not ID.fullmatch(run_id) or not ID.fullmatch(job_id) or run_id==job_id or not 1<=len(registration_versions)<=500:
        raise ValueError('derivative_run_scope')
    b=owner.original_batch();store=AppendResearchStore(config)
    request=dict(contract=CONTRACT,review_digest=digest(b),run_id=run_id,versions=registration_versions,cutoff=cutoff)
    if metrics is not None:
        if not isinstance(metrics,(list,tuple)) or not metrics or len(set(metrics))!=len(metrics) or not set(metrics)<={'FY1_EPS','FPER'}:
            raise ValueError('bounded_dated_metric_selection')
        request['metrics']=sorted(metrics)
    with store.atomic_job(job_id,request) as cell:
        with store.connect() as c:
            exists=c.execute('SELECT run_id FROM research_run WHERE run_id=?',(run_id,)).fetchone()
            if not exists and c.execute('SELECT count(*) FROM research_run').fetchone()[0]>=16:
                raise ValueError('composite_run_bound_exceeded')
            _append(c,'research_run',('run_id','started_at','as_of','status'),
                (run_id,cutoff,cutoff,'DERIVED_DATED_RESEARCH_NOT_NEW_CAPTURE'),already_committed=bool(cell['previous']))
            observations=[]
            for ticker,version in sorted(registration_versions.items()):
                registration=current_identity(store,ticker)
                entry=next(e for e in b['entries'] if e['security']['ticker']==ticker)
                security=bind_current_identity(entry['security'],registration,expected_version=version)
                source_id=source_custody(store,owner,security)
                snaps=owner.snapshots(security=security,cutoff=cutoff)
                if metrics is not None:
                    snaps=[s for s in snaps if s['metric'] in metrics]
                    if {s['metric'] for s in snaps}!=set(metrics):raise ValueError('requested_dated_metric_not_eligible')
                if not snaps:raise ValueError('no_dated_numeric_eligibility')
                capsule=owner.capsule(security);raw=encoded(capsule);sha=digest(raw)
                path=plain(store.path.parent/'raw'/sha);path.parent.mkdir(mode=0o700,exist_ok=True)
                if not path.exists():
                    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
                    with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
                if path.stat().st_nlink!=1 or path.read_bytes()!=raw:raise ValueError('derived_capsule_integrity')
                key=digest([CONTRACT,ticker]);ident=digest([run_id,CONTRACT,key])
                receipt=dict(contract=CONTRACT,kind='DERIVED_MULTIPARENT_NOT_HTTP',captured_at=cutoff,
                    raw_sha256=sha,run_id=run_id,original_source_capture_id=source_id,job_id=job_id,
                    review_digest=digest(b),recollected=False)
                _append(c,'source_capture',('capture_id','run_id','provider','request_key','raw_sha','raw_path','captured_at','receipt_json'),
                    (ident,run_id,'KISMultisourceResearch',key,sha,str(path),cutoff,encoded(receipt).decode()),already_committed=bool(cell['previous']))
                for snapshot in snaps:
                    field='valuation.'+snapshot['metric'];oid=digest([run_id,ticker,field,sha])
                    payload=dict(snapshot=snapshot,strict_native=False,research_only=True,import_contract=CONTRACT,
                        registration_version=version,ingestion_job=job_id,original_source_capture_id=source_id)
                    _append(c,'research_observation',('observation_id','run_id','ticker','field','status','source_sha','payload_json'),
                        (oid,run_id,ticker,field,'SOURCE_REFERENCE',sha,encoded(payload).decode()),already_committed=bool(cell['previous']))
                    observations.append(dict(observation_id=oid,ticker=ticker,metric=snapshot['metric'],
                        snapshot_sha256=digest(snapshot),capsule_sha256=sha,source_capture_id=source_id))
            owner.original_batch()
        result=dict(contract=CONTRACT,run_id=run_id,review_digest=digest(b),observations=observations,strict_native=False,send=False)
        if cell['previous'] and cell['previous']['result']!=result:raise ValueError('multisource_replay_changed')
        cell['result']=result
        return result


def verify_stored(store,owner,*,row,payload,capsule,security,cutoff):
    if not isinstance(owner,ReviewedMultisourceKIS):raise ValueError('live_multisource_capability_required')
    snapshot=owner.verify(capsule,payload['snapshot'],security=security,cutoff=cutoff)
    source_id=source_custody(store,owner,security)
    if payload.get('original_source_capture_id')!=source_id:raise ValueError('numeric_original_capture_binding')
    with store.connect() as c:
        journal=c.execute('SELECT value FROM research_meta WHERE key=?',
            ('vnext-runtime-v1:job:'+payload['ingestion_job'],)).fetchone()
    if not journal:raise ValueError('committed_multisource_journal_required')
    j=json.loads(journal[0]);expected=dict(observation_id=row[0],ticker=row[2],metric=snapshot['metric'],
        snapshot_sha256=digest(snapshot),capsule_sha256=row[5],source_capture_id=source_id)
    if (j['status']!='COMMITTED' or j['result']['review_digest']!=capsule['review_digest']
            or j['result']['run_id']!=row[1] or expected not in j['result']['observations']
            or row[3]!='valuation.'+snapshot['metric'] or row[4]!='SOURCE_REFERENCE'):
        raise ValueError('multisource_journal_or_field_binding')
    return snapshot
