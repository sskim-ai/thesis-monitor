"""Fresh-process sealed-byte consumption, never live capability reissuance."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = Path(sys.argv[1]); expected = sys.argv[2]
    if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('cold_plain_input_required')
    if path.stat().st_size>4*1024**2:raise ValueError('cold_input_size')
    raw = path.read_bytes()
    if len(raw)>4*1024**2 or hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError('cold_input_identity')
    data = json.loads(raw)
    own=Path(__file__);own_raw=own.read_bytes()
    if data['source_pins'].get(str(own.relative_to(ROOT)))!=dict(bytes=len(own_raw),sha256=hashlib.sha256(own_raw).hexdigest()):
        raise ValueError('cold_consumer_pin')
    count={'official-issued-source-cold-v1':2,'official-issued-source-cold-kr-v3':1}.get(data['contract'])
    if count is None or len(data['already_issued_source_receipts'])!=count:
        raise ValueError('cold_source_provenance_required')
    if count==1 and any(d['market'] not in ('kr','global') for d in data['plan']['descriptors']):
        raise ValueError('cold_kr_only_plan')
    def guard(event,args):
        if event.startswith('socket.') or event in ('sqlite3.connect','subprocess.Popen','os.system','os.fork'):
            raise PermissionError('cold_no_external_io')
        if event=='open' and isinstance(args[0],(str,bytes)):
            p=Path(os.fsdecode(args[0])).absolute()
            if (p.name.startswith('.env') or p.name in ('auth.json','auth.toml')
                    or p.suffix in ('.db','.sqlite','.sqlite3','.pem','.key')
                    or args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)):
                raise PermissionError('cold_readonly_public_evidence')
    sys.addaudithook(guard)
    sys.path.insert(0,str(ROOT))
    # Check and compile the pinned loader bytes before importing any app code.
    loader_name='scripts/official_scoped_source_parent.py'
    loader_path=ROOT/loader_name
    if any(p.is_symlink() for p in (loader_path,*loader_path.parents)):raise ValueError('cold_loader_path')
    loader=loader_path.read_bytes()
    if data['source_pins'][loader_name]!=dict(bytes=len(loader),sha256=hashlib.sha256(loader).hexdigest()):
        raise ValueError('cold_loader_pin')
    scope={'__file__':str(loader_path),'__name__':'cold_pinned_loader'}
    exec(compile(loader,str(loader_path),'exec',dont_inherit=True),scope)
    sys.meta_path.insert(0,scope['PinnedApplicationImports'](data))
    from app.services.sealed_fresh_dispatch import consume_bound_result
    from app.services.unified_snapshot_contract import digest
    accepted=[]
    for key,sha in data['receipts'].items():
        value=consume_bound_result(root=data['capture'],plan=data['plan'],logical_id=key,receipt_sha256=sha)
        accepted.append(dict(logical_id=key,normalization_sha256=digest(value)))
    root=Path(data['capture'])
    if not root.is_absolute() or any(p.is_symlink() for p in (root,*root.parents)):
        raise ValueError('cold_capture_path')
    roles=[]; entries=set()
    for receipt,artifact in zip(data['already_issued_source_receipts'],data['row_artifacts'],strict=True):
        if count==1 and not receipt['entry_id'].startswith('kr:'):
            raise ValueError('cold_kr_only_scope')
        value=dict(receipt);receipt_sha=value.pop('receipt_sha256')
        if digest(value)!=receipt_sha or receipt['entry_id']!=artifact['entry_id']:
            raise ValueError('cold_issued_receipt_identity')
        if (receipt['consumer']!='SCOPED_SOURCE_ONLY' or receipt['allowed_use']!='BOUND_SOURCE_ROWS_ONLY'
                or receipt['generation_id']!=data['plan']['generation_id']
                or receipt['plan_sha256']!=digest(data['plan'])
                or receipt['parent_receipt_sha256']!=data['plan']['parent_receipt_sha256']
                or receipt['entry_id'] in entries
                or any(receipt[k] is not False for k in ('technical_signal','completed_price_authority',
                    'financial_use','valuation_use','economic_use','D01_D02','native_use','full22_native','model_use'))):
            raise ValueError('cold_source_scope')
        entries.add(receipt['entry_id'])
        raw_hashes=[]
        for key in data['receipts']:
            if key.startswith(receipt['entry_id']+':page'):
                final=json.loads((root/'receipts'/key/'final.json').read_bytes())
                raw_hashes.append(final['raw_sha256'])
        if sorted(raw_hashes)!=sorted(receipt['raw_sha256']):raise ValueError('cold_source_page_binding')
        rows_path=root/artifact['path']
        if (Path(artifact['path']).is_absolute() or '..' in Path(artifact['path']).parts
                or any(p.is_symlink() for p in (rows_path,*rows_path.parents)) or rows_path.stat().st_size>8*1024**2):
            raise ValueError('cold_rows_path')
        body=rows_path.read_bytes();rows=json.loads(body)
        if (hashlib.sha256(body).hexdigest()!=artifact['sha256'] or digest(rows)!=receipt['normalized_sha256']
                or len(rows)!=receipt['rows'] or len(rows)!=receipt['requested_rows']):
            raise ValueError('cold_issued_rows_identity')
        roles.append(dict(entry_id=receipt['entry_id'],rows=len(rows),normalized_sha256=digest(rows)))
    return dict(status='ORIGINAL_SEALED_BYTE_CONSUMER_PASS_NOT_OWNER_REISSUANCE',
        pid=os.getpid(),input_sha256=expected,receipt_set_sha256=digest(data['receipts']),
        accepted=accepted,roles=roles,new_live_authority=False,DB=0,HTTP=0,models=0,native=False)


if __name__=='__main__':
    try: print(json.dumps(main(),sort_keys=True))
    except Exception as exc:
        print(json.dumps(dict(status='COLD_DENIED',error_type=type(exc).__name__)))
        raise SystemExit(2)
