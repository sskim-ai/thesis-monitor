"""Manual append-only import from a backend-reviewed original public capture.

The bootstrap callback is trusted local operator code, not model/request JSON.
Checksums prove integrity, not authority. Original validators decide eligibility.
"""
from copy import deepcopy
from datetime import datetime
import os
import sqlite3

from app.services.vnext_research_store import digest, encoded, plain
from app.services.vnext_runtime import RuntimeStore, ID

CONTRACT = 'vnext-reviewed-valuation-ingestion-v1'
IDENTITY = ('ticker','canonical_security_id','canonical_company_id','company_name',
            'country','exchange','security_type','issuer_type','cik','corp_code',
            'ordinary_share_identifier','adr_ratio','adr_ratio_source','adr_ratio_as_of')
PUBLIC_COLUMNS = (*IDENTITY, 'updated_at')
RESEARCH_TABLES = {'research_meta','research_run','source_capture','research_observation'}


def current_identity(store, ticker):
    with store.connect() as c:
        rows = c.execute('SELECT '+','.join('s.'+k for k in PUBLIC_COLUMNS)+
            ' FROM securitymaster s JOIN watchlistitem w ON w.ticker=s.ticker'
            ' WHERE s.ticker=? AND w.active=1', (ticker,)).fetchall()
    if len(rows) != 1:
        raise ValueError('current_public_registration_missing_or_ambiguous')
    row = dict(zip(PUBLIC_COLUMNS, rows[0]))
    required = ('ticker','canonical_security_id','canonical_company_id','company_name',
                'country','exchange','security_type','issuer_type','updated_at')
    if any(not isinstance(row.get(k),str) or not row[k].strip() for k in required):
        raise ValueError('current_public_registration_incomplete')
    if row['issuer_type'].lower() in ('unknown','unverified'):
        raise ValueError('current_public_registration_unqualified')
    return dict(contract='current-public-valuation-identity-v1',security={k:row[k] for k in IDENTITY},
        registration_version=digest(row),registered_at_version=row['updated_at'])


def bind_current_identity(envelope, registration, *, expected_version):
    if (registration.get('contract')!='current-public-valuation-identity-v1' or
        registration.get('registration_version')!=expected_version):
        raise ValueError('current_registration_version_changed')
    current = registration['security']
    required = ('ticker','canonical_security_id','canonical_company_id','country','exchange','security_type','issuer_type')
    if any(not envelope.get(k) or envelope[k]!=current.get(k) for k in required):
        raise ValueError('current_registration_identity_mismatch')
    if any(envelope[k]!=current[k] for k in set(envelope)&set(current)):
        raise ValueError('current_registration_metadata_conflict')
    return dict(current)


class AppendResearchStore(RuntimeStore):
    """Narrower SQL permissions than the general worker; INSERT only."""
    @staticmethod
    def _authorizer(write):
        def check(action, first, second, db, trigger):
            if trigger is not None:return sqlite3.SQLITE_DENY
            allowed = action in (sqlite3.SQLITE_SELECT,sqlite3.SQLITE_TRANSACTION,sqlite3.SQLITE_FUNCTION,sqlite3.SQLITE_RECURSIVE)
            allowed |= action==sqlite3.SQLITE_READ and (db=='main' or db is None and second=='') and (
                first in (*RESEARCH_TABLES,'sqlite_master') or
                first=='securitymaster' and second in PUBLIC_COLUMNS or
                first=='watchlistitem' and second in ('ticker','active'))
            allowed |= write and action==sqlite3.SQLITE_INSERT and db=='main' and first in RESEARCH_TABLES
            return sqlite3.SQLITE_OK if allowed else sqlite3.SQLITE_DENY
        return check


def _append(c, table, columns, values, *, already_committed=False):
    # Compare every stored byte, not just the primary key or raw SHA.
    names=','.join(columns)
    old=c.execute('SELECT '+names+' FROM '+table+' WHERE '+columns[0]+'=?',(values[0],)).fetchone()
    if old is not None:
        if tuple(values)!=old:raise ValueError('append_conflict:'+table)
        return False
    if already_committed:raise ValueError('committed_row_missing:'+table)
    c.execute('INSERT INTO '+table+' ('+names+') VALUES ('+','.join('?' for _ in values)+')',values)
    return True


def ingest_reviewed_kis(config, *, job_id, reviewed_capture, expected_capture_digest,
                        expected_registration_version, cutoff):
    """Same insert-only journal and CAS; no registration or existing-row edits."""
    from app.services.vnext_kis_research import reviewed_batch, CONTRACT as kis_contract
    if not callable(reviewed_capture):raise ValueError('backend_kis_owner_replay_capability_required')
    initial=deepcopy(reviewed_capture());store=AppendResearchStore(config)
    request=dict(contract=kis_contract,original_capture_sha256=expected_capture_digest,
                 registration_version=expected_registration_version,cutoff=cutoff)
    with store.atomic_job(job_id,request) as cell:
        registration=current_identity(store,initial['security']['ticker'])
        security=bind_current_identity(initial['security'],registration,expected_version=expected_registration_version)
        batch,snapshots=reviewed_batch(lambda:initial,expected_digest=expected_capture_digest,security=security,cutoff=cutoff)
        run=batch['run']
        if not ID.fullmatch(run['run_id']) or run['run_id']==job_id:raise ValueError('original_run_identity_required')
        capsule=batch['capsule'];raw=encoded(capsule);sha=digest(raw)
        projection=dict(provider='KISOwnerReplay',request_key=digest([kis_contract,security['ticker']]),raw=raw.decode(),
            receipt=dict(raw_sha256=sha,run_id=run['run_id'],captured_at=cutoff,kind='ORIGINAL_OWNER_REPLAY',source_generation=run['run_id']))
        with store.connect() as c:
            _append(c,'research_run',('run_id','started_at','as_of','status'),[run[k] for k in ('run_id','started_at','as_of','status')],already_committed=bool(cell['previous']))
            for item in [*batch['captures'],projection]:
                body=item['raw'].encode();h=digest(body);path=plain(store.path.parent/'raw'/h);path.parent.mkdir(mode=0o700,exist_ok=True)
                if not path.exists():
                    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
                    with os.fdopen(fd,'wb') as f:f.write(body);f.flush();os.fsync(f.fileno())
                if not path.is_file() or path.stat().st_nlink!=1 or path.read_bytes()!=body:raise ValueError('canonical_raw_integrity_gap')
                ident=digest([run['run_id'],item['provider'],item['request_key']])
                _append(c,'source_capture',('capture_id','run_id','provider','request_key','raw_sha','raw_path','captured_at','receipt_json'),
                    (ident,run['run_id'],item['provider'],item['request_key'],h,str(path),item['receipt']['captured_at'],encoded(item['receipt']).decode()),already_committed=bool(cell['previous']))
            observations=[]
            for snapshot in snapshots:
                field='valuation.'+snapshot['metric'];ident=digest([run['run_id'],security['ticker'],field,sha])
                payload=dict(snapshot=snapshot,strict_native=False,research_only=True,import_contract=kis_contract,registration_version=expected_registration_version)
                _append(c,'research_observation',('observation_id','run_id','ticker','field','status','source_sha','payload_json'),
                    (ident,run['run_id'],security['ticker'],field,'SOURCE_REFERENCE',sha,encoded(payload).decode()),already_committed=bool(cell['previous']))
                observations.append(dict(observation_id=ident,metric=snapshot['metric'],snapshot_sha256=digest(snapshot)))
        result=dict(contract=kis_contract,source_run=run['run_id'],ingestion_job=job_id,observations=observations,
                    capsule_sha256=sha,registration=registration,strict_native=False,send=False)
        if cell['previous'] and cell['previous']['result']!=result:raise ValueError('persisted_replay_changed')
        cell['result']=result
        return result


def ingest_reviewed_valuation(config, *, job_id, reviewed_capture, expected_capture_digest,
                             expected_registration_version, cutoff, reviewed_alias_owner=None):
    """Original run stays original; all DB rows and journal commit atomically.

    CAS files are immutable; failed imports can leave bounded orphan blobs.
    No registration, thesis, existing observation or old database is modified.
    """
    if not callable(reviewed_capture):raise ValueError('backend_reviewed_capture_callback_required')
    batch=deepcopy(reviewed_capture())
    if digest(batch)!=expected_capture_digest:raise ValueError('reviewed_capture_changed')
    run=batch['run']
    if not ID.fullmatch(run['run_id']) or run['run_id']==job_id:raise ValueError('original_run_identity_required')
    if not 0<len(batch['captures'])<=7:raise ValueError('bounded_valuation_capture_required')
    store=AppendResearchStore(config)
    request=dict(contract=CONTRACT,original_capture_sha256=expected_capture_digest,
                 registration_version=expected_registration_version,cutoff=cutoff)
    if reviewed_alias_owner is not None:
        from app.services.reviewed_security_alias import ReviewedSecurityAliases
        if not isinstance(reviewed_alias_owner,ReviewedSecurityAliases):raise ValueError('backend_alias_owner_required')
        request['alias_review_sha256']=reviewed_alias_owner.binding_digest()
    with store.atomic_job(job_id,request) as cell:
        registration=current_identity(store,batch['security']['ticker'])
        security=bind_current_identity(batch['security'],registration,expected_version=expected_registration_version)
        with store.connect() as c:
            _append(c,'research_run',('run_id','started_at','as_of','status'),[run[k] for k in ('run_id','started_at','as_of','status')],already_committed=bool(cell['previous']))
            originals=[]
            for item in batch['captures']:
                raw=item['raw'].encode('utf-8');receipt=item['receipt'];sha=digest(raw)
                if (len(raw)>2*1024**2 or receipt.get('raw_sha256')!=sha or receipt.get('raw_bytes')!=len(raw) or
                    receipt.get('run_id')!=run['run_id'] or receipt.get('provider')!='Kiwoom' or item['provider']!='Kiwoom' or
                    receipt.get('auth') is not False or receipt.get('raw_birth')!='CURRENT_HTTP' or
                    receipt.get('status')!=200 or receipt.get('api') not in ('ka10099','ka10001') or
                    receipt.get('request_key')!=item['request_key'] or digest(receipt['request'])!=item['request_key']):
                    raise ValueError('original_public_capture_binding')
                path=plain(store.path.parent/'raw'/sha);path.parent.mkdir(mode=0o700,exist_ok=True)
                if not path.exists():
                    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
                    with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
                if not path.is_file() or path.stat().st_nlink!=1 or path.read_bytes()!=raw:raise ValueError('canonical_raw_integrity_gap')
                ident=digest([run['run_id'],item['provider'],item['request_key']])
                _append(c,'source_capture',('capture_id','run_id','provider','request_key','raw_sha','raw_path','captured_at','receipt_json'),
                    (ident,run['run_id'],item['provider'],item['request_key'],sha,str(path),receipt['captured_at'],encoded(receipt).decode()),already_committed=bool(cell['previous']))
                originals.append(dict(raw_sha256=sha,receipt_sha256=digest(receipt)))
            from app.services.vnext_legacy_reuse import native_valuation_inputs
            from app.services.provider_native_valuation_snapshot import derive_provider_snapshots
            inputs=native_valuation_inputs(store,run['run_id'],security,'kiwoom',market_type=batch['market_type'],cutoff=datetime.fromisoformat(cutoff))
            if reviewed_alias_owner is not None:
                inputs['identity_inputs']['reviewed_alias_owner']=reviewed_alias_owner
            snapshots=[v.model_dump(mode='json') if hasattr(v,'model_dump') else v for v in derive_provider_snapshots(inputs,security=security,run_id=run['run_id'])]
            if {s['metric'] for s in snapshots}!={'PER','PBR'} or any(not s['display_eligible'] for s in snapshots):
                raise ValueError('original_provider_snapshot_not_eligible')
            observations=[]
            for s in snapshots:
                field='valuation.'+s['metric'];sha=s['raw_sha256'];ident=digest([run['run_id'],security['ticker'],field,sha])
                payload=dict(snapshot=s,strict_native=False,current_capture=False,source_captured_at=s['retrieval_timestamp'],
                    research_only=True,import_contract=CONTRACT,registration_version=expected_registration_version)
                _append(c,'research_observation',('observation_id','run_id','ticker','field','status','source_sha','payload_json'),
                    (ident,run['run_id'],security['ticker'],field,'SOURCE_REFERENCE',sha,encoded(payload).decode()),already_committed=bool(cell['previous']))
                observations.append(dict(observation_id=ident,metric=s['metric'],snapshot_sha256=s['snapshot_sha256']))
        result=dict(contract=CONTRACT,source_run=run['run_id'],ingestion_job=job_id,original_captures=originals,
            observations=observations,registration=registration,recollected=False,strict_native=False,send=False)
        if cell['previous'] and cell['previous']['result']!=result:raise ValueError('persisted_replay_changed')
        cell['result']=result
        return result
