"""Insert-only dated source custody. Never creates a financial observation."""
import json
import os
from app.services.vnext_kis_source_state import ReviewedKISSourceObservations, SourceState, CONTRACT
from app.services.vnext_research_store import digest, encoded, plain
from app.services.vnext_research_ingestion import AppendResearchStore,current_identity,bind_current_identity,_append
from app.services.vnext_runtime import ID


def _capture(item, batch):
    original=item['receipt'];run=batch['plan']['generation_id'];key=digest(item['request'])
    receipt=dict(contract=CONTRACT,kind='SOURCE_PRESENT_NOT_OWNER',provider='KIS',run_id=run,
        captured_at=original['ended_at'],raw_sha256=original['raw_sha256'],request_key=key,
        original_receipt=original,original_receipt_sha256=digest(original),
        original_archive_sha256=batch['archive_sha256'],recollected=False,numeric_use=False,direction_use=False)
    return digest([run,'KIS',key]),key,receipt


def ingest_sources(config, *, owner, job_id, registration_versions, cutoff):
    if not isinstance(owner,ReviewedKISSourceObservations):raise ValueError('reviewed_source_capability_required')
    batch=owner.original_batch();run=batch['plan']['generation_id'];store=AppendResearchStore(config)
    if not ID.fullmatch(run) or run==job_id or not 1<=len(registration_versions)<=500:
        raise ValueError('original_source_run_and_subjects_required')
    request=dict(contract=CONTRACT,source_digest=digest(batch),versions=registration_versions,cutoff=cutoff)
    with store.atomic_job(job_id,request) as cell:
        with store.connect() as c:
            exists=c.execute('SELECT run_id FROM research_run WHERE run_id=?',(run,)).fetchone()
            if not exists and c.execute('SELECT count(*) FROM research_run').fetchone()[0]>=16:
                raise ValueError('composite_run_bound_exceeded')
            _append(c,'research_run',('run_id','started_at','as_of','status'),
                (run,batch['plan']['as_of'],max(x['receipt']['ended_at'] for x in batch['captures']),'ORIGINAL_SOURCE_ONLY'),already_committed=bool(cell['previous']))
            rows=[]
            for ticker,version in sorted(registration_versions.items()):
                item=next(x for x in batch['captures'] if x['security']['ticker']==ticker)
                registration=current_identity(store,ticker)
                security=bind_current_identity(item['security'],registration,expected_version=version)
                value=owner.project(security=security,as_of=cutoff)
                if value['state']!=SourceState.PRESENT.value:raise ValueError('positive_source_only_append')
                ident,key,receipt=_capture(item,batch);raw=item['raw'].encode();sha=digest(raw)
                path=plain(store.path.parent/'raw'/sha);path.parent.mkdir(mode=0o700,exist_ok=True)
                if not path.exists():
                    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
                    with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
                if not path.is_file() or path.stat().st_nlink!=1 or path.read_bytes()!=raw:raise ValueError('canonical_raw_integrity_gap')
                _append(c,'source_capture',('capture_id','run_id','provider','request_key','raw_sha','raw_path','captured_at','receipt_json'),
                    (ident,run,'KIS',key,sha,str(path),receipt['captured_at'],encoded(receipt).decode()),already_committed=bool(cell['previous']))
                rows.append(dict(ticker=ticker,capture_id=ident,raw_sha=sha,original_receipt_sha=digest(item['receipt']),kind='SOURCE_PRESENT_NOT_OWNER'))
        result=dict(contract=CONTRACT,original_run=run,rows=rows,new_numeric_observations=0,source_digest=digest(batch),send=False)
        if cell['previous'] and cell['previous']['result']!=result:raise ValueError('source_replay_changed')
        cell['result']=result
        return result


class StoredKISSourceObservations(ReviewedKISSourceObservations):
    """Cold lookup requires the original reviewed capability AND committed custody."""
    def __init__(self,store,owner,job_id):
        if not isinstance(owner,ReviewedKISSourceObservations):raise ValueError('original_review_required')
        self._store,self._original,self._job=store,owner,job_id
        super().__init__(owner.original_batch)

    def project(self,*,security,as_of):
        value=super().project(security=security,as_of=as_of)
        if value is None:return None
        with self._store.connect() as c:
            journal=c.execute('SELECT value FROM research_meta WHERE key=?',('vnext-runtime-v1:job:'+self._job,)).fetchone()
            if not journal:raise ValueError('committed_source_job_required')
            result=json.loads(journal[0])
            if result['status']!='COMMITTED' or result['result']['source_digest']!=self._pin:raise ValueError('source_journal_binding')
            match=[r for r in result['result']['rows'] if r['ticker']==security['ticker']]
            if not match:return value
            item=next(i for i in self.original_batch()['captures'] if i['security']['ticker']==security['ticker'])
            ident,key,receipt=_capture(item,self.original_batch())
            row=c.execute('SELECT capture_id,run_id,provider,request_key,raw_sha,raw_path,captured_at,receipt_json FROM source_capture WHERE capture_id=?',(ident,)).fetchone()
            path=plain(self._store.path.parent/'raw'/value['source_sha256'])
            expected=(ident,value['source_generation'],'KIS',key,value['source_sha256'],str(path),value['captured_at'],encoded(receipt).decode())
            if row!=expected or not path.is_file() or path.stat().st_nlink!=1 or path.read_bytes()!=item['raw'].encode():raise ValueError('stored_original_capture_changed')
        return dict(value,private_durable=True,durability_scope='RAW_SOURCE_ONLY_NO_FINANCIAL_OBSERVATION',source_capture_id=ident)
