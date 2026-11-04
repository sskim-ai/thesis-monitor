"""Append a backend-replayed public refresh; never an operating or model API.

The reviewer replays original source validators in trusted code. This module only
owns exact registration, immutable bytes, quotas and the existing atomic journal.
"""
from copy import deepcopy
import os
from app.services.vnext_research_ingestion import AppendResearchStore,current_identity,_append
from app.services.vnext_research_store import digest,encoded,plain,STATES
from app.services.vnext_runtime import ID

CONTRACT='reviewed-public-refresh-ingestion-v1'
COLUMNS={
    'research_run':('run_id','started_at','as_of','status'),
    'source_capture':('capture_id','run_id','provider','request_key','raw_sha','raw_path','captured_at','receipt_json'),
    'research_observation':('observation_id','run_id','ticker','field','status','source_sha','payload_json')}

class ReviewedPublicRefresh:
    def __init__(self,trusted_replay):
        if not callable(trusted_replay):raise ValueError('trusted_source_replay_required')
        self._read=trusted_replay;self._pin=digest(trusted_replay());self._revoked=False
    def revoke(self):self._revoked=True
    def batch(self):
        b=deepcopy(self._read())
        if self._revoked or digest(b)!=self._pin:raise ValueError('refresh_changed_or_revoked')
        if b.get('contract')!=CONTRACT or b.get('original_validator_replay') is not True:
            raise ValueError('original_validator_replay_required')
        database_payload=dict(b,captures=[{k:v for k,v in c.items() if k!='raw'} for c in b['captures']])
        if len(b['runs'])>8 or len(b['captures'])>600 or len(b['observations'])>746 or len(encoded(database_payload))>120*1024**2:
            raise ValueError('refresh_record_or_payload_limit')
        runs={r['run_id'] for r in b['runs']};caps={}
        if len(runs)!=len(b['runs']) or any(not ID.fullmatch(r) for r in runs):raise ValueError('refresh_run_identity')
        for c in b['captures']:
            raw=c['raw'].encode();r=c['receipt']
            if (c['run_id'] not in runs or digest(raw)!=c['raw_sha'] or c['capture_id']!=digest([c['run_id'],c['provider'],c['request_key']])
                or r.get('auth') is True or not r.get('captured_at') or len(raw)>64*1024**2):raise ValueError('refresh_capture_binding')
            key=(c['run_id'],c['raw_sha']);caps[key]=raw
        if len({c['capture_id'] for c in b['captures']})!=len(b['captures']):raise ValueError('duplicate_refresh_capture')
        if sum(len(v) for v in {digest(v):v for v in caps.values()}.values())>1024**3:raise ValueError('refresh_CAS_limit')
        for o in b['observations']:
            p=o['payload'];ticker=o['ticker']
            if (ticker not in b['registrations'] and ticker not in ('@MARKET:KR','@MARKET:US')
                or o['status'] not in STATES or (o['run_id'],o['source_sha']) not in caps or p.get('strict_native') is not False
                or any(k in p for k in ('accepted_Core','accepted_receipt'))
                or o['observation_id']!=digest([o['run_id'],ticker,o['field'],o['source_sha']])):raise ValueError('refresh_observation_membership')
        if len({o['observation_id'] for o in b['observations']})!=len(b['observations']):raise ValueError('duplicate_refresh_observation')
        return b

def ingest(config,*,owner,job_id,approved_batch_sha256):
    if not isinstance(owner,ReviewedPublicRefresh):raise ValueError('live_refresh_review_capability_required')
    b=owner.batch()
    if digest(b)!=approved_batch_sha256:raise ValueError('approved_refresh_digest_mismatch')
    store=AppendResearchStore(config)
    request=dict(contract=CONTRACT,batch_sha256=approved_batch_sha256)
    with store.atomic_job(job_id,request) as cell:
        for code,expected in b['registrations'].items():
            if current_identity(store,code)!=expected:raise ValueError('refresh_registration_changed')
        committed=bool(cell['previous']);counts=dict(research_run=0,source_capture=0,research_observation=0)
        with store.connect() as c:
            for r in b['runs']:
                _append(c,'research_run',COLUMNS['research_run'],[r[k] for k in COLUMNS['research_run']],already_committed=committed)
                counts['research_run']+=1
            for item in b['captures']:
                raw=item['raw'].encode();h=digest(raw);path=plain(store.path.parent/'raw'/h)
                path.parent.mkdir(mode=0o700,exist_ok=True)
                if not path.exists():
                    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
                    with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
                if path.stat().st_nlink!=1 or path.read_bytes()!=raw:raise ValueError('refresh_canonical_raw_corruption')
                r=dict(item,raw_path=str(path),captured_at=item['receipt']['captured_at'],receipt_json=encoded(item['receipt']).decode())
                _append(c,'source_capture',COLUMNS['source_capture'],[r[k] for k in COLUMNS['source_capture']],already_committed=committed)
                counts['source_capture']+=1
            for item in b['observations']:
                r=dict(item,payload_json=encoded(item['payload']).decode())
                _append(c,'research_observation',COLUMNS['research_observation'],[r[k] for k in COLUMNS['research_observation']],already_committed=committed)
                counts['research_observation']+=1
        result=dict(contract=CONTRACT,batch_sha256=approved_batch_sha256,rows=counts,strict_native=False,send=False)
        if cell['previous'] and cell['previous']['result']!=result:raise ValueError('refresh_committed_result_drift')
        cell['result']=result
        return result
