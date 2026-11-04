"""Separate read-only process for original per-role receipts of a P3 batch."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    path=Path(sys.argv[1]);raw=path.read_bytes()
    if len(raw)>4*1024**2 or hashlib.sha256(raw).hexdigest()!=sys.argv[2]:
        raise ValueError('p3_cold_input')
    data=json.loads(raw)
    def guard(event,args):
        if event.startswith('socket.') or event in ('sqlite3.connect','subprocess.Popen','os.system','os.fork'):
            raise PermissionError('p3_cold_no_external_io')
        if event=='open' and isinstance(args[0],(str,bytes)):
            p=Path(os.fsdecode(args[0]))
            if p.name.startswith('.env') or p.name in ('auth.json','auth.toml') or p.suffix in ('.db','.sqlite','.sqlite3','.pem','.key'):
                raise PermissionError('p3_cold_protected_path')
            if args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):
                raise PermissionError('p3_cold_readonly')
    sys.addaudithook(guard)
    for name in ('scripts/official_source_batch_cold.py','app/services/registered_source_batch.py',
                 'scripts/official_scoped_source_parent.py'):
        p=ROOT/name;body=p.read_bytes()
        if data['source_pins'].get(name)!=dict(bytes=len(body),sha256=hashlib.sha256(body).hexdigest()):
            raise ValueError('p3_cold_code_pin')
    loader=ROOT/'scripts/official_scoped_source_parent.py'
    scope={'__file__':str(loader),'__name__':'p3_cold_pinned_loader'}
    exec(compile(loader.read_bytes(),str(loader),'exec',dont_inherit=True),scope)
    sys.path.insert(0,str(ROOT));sys.meta_path.insert(0,scope['PinnedApplicationImports'](data))
    from app.services.sealed_fresh_dispatch import consume_bound_result
    from app.services.registered_source_batch import validate_cold_roles,digest
    root=Path(data['capture'])
    if not root.is_absolute() or any(p.is_symlink() for p in (root,*root.parents)):
        raise ValueError('p3_cold_capture')
    for key,receipt in data['physical_receipts'].items():
        consume_bound_result(root=root,plan=data['plan'],logical_id=key,receipt_sha256=receipt)
    def rows(artifact):
        relative=Path(artifact['path']);p=root/relative
        if relative.is_absolute() or '..' in relative.parts or any(x.is_symlink() for x in (p,*p.parents)) or p.stat().st_size>32*1024**2:
            raise ValueError('p3_cold_row_path')
        body=p.read_bytes();return body,json.loads(body)
    for receipt in data['receipts']:
        hashes=[]
        for key in data['physical_receipts']:
            if key.startswith(receipt['entry_id']+':page'):
                final=json.loads((root/'receipts'/key/'final.json').read_bytes())
                hashes.append(final['raw_sha256'])
        if sorted(hashes)!=sorted(receipt['raw_sha256']):raise ValueError('p3_cold_original_page_binding')
    wm_context=None
    if any(r.get('contract')=='current-scoped-role-source-receipt-v2-wm' for r in data['receipts']):
        stocks=root.parent/'worker'/'stocks'
        if not stocks.is_dir() or any(p.is_symlink() for p in (stocks,*stocks.parents)):
            raise ValueError('p3_cold_wm_stock_root')
        raw_paths={}
        for key in data['physical_receipts']:
            final=json.loads((root/'receipts'/key/'final.json').read_bytes())
            if key!='kiwoom:auth':
                relative=Path(final['attempts'][-1]['artifact'])
                if relative.is_absolute() or '..' in relative.parts:
                    raise ValueError('p3_cold_wm_raw_escape')
                raw_paths[final['raw_sha256']]=root/relative
        def sealed_raw(sha):
            p=raw_paths[sha]
            if not p.is_relative_to(root) or any(x.is_symlink() for x in (p,*p.parents)) or p.stat().st_size>4*1024**2:
                raise ValueError('p3_cold_wm_raw_path')
            raw=p.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('p3_cold_wm_raw_hash')
            return raw
        wm_context=dict(stocks_root=stocks,external_root=data['external_root'],sealed_raw=sealed_raw,
            expected_parser_pins=data['external_pins'])
    result=validate_cold_roles(data,rows,wm_context=wm_context)
    result.update(pid=os.getpid(),input_sha256=hashlib.sha256(raw).hexdigest(),
        receipt_set_sha256=digest(data['physical_receipts']),HTTP=0,DB=0,models=0,
        test_only=data.get('test_only',False))
    return result


if __name__=='__main__':
    try:print(json.dumps(main(),sort_keys=True))
    except Exception as exc:
        print(json.dumps(dict(status='P3_COLD_DENIED',error_type=type(exc).__name__)))
        raise SystemExit(2)
