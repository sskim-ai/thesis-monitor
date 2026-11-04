"""Networkless exact-source parser process, without credentials or owner issuance."""
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys

root=Path(sys.argv[1]).resolve();pins=json.loads(Path(sys.argv[2]).read_bytes())
sys.path.insert(0,sys.argv[3])
os.environ.update(THESIS_MONITOR_ENV_FILE='',DATABASE_URL='sqlite://')

class Pinned(importlib.abc.MetaPathFinder,importlib.abc.Loader):
    def find_spec(self,name,path=None,target=None):
        if name!='app' and not name.startswith('app.'):return None
        names=[n for n in (name.replace('.','/')+'.py',name.replace('.','/')+'/__init__.py') if n in pins]
        if len(names)!=1:raise PermissionError('unapproved_parser_dependency')
        n=names[0]
        return importlib.util.spec_from_file_location(name,root/n,loader=self,submodule_search_locations=[] if n.endswith('/__init__.py') else None)
    def create_module(self,spec):return None
    def exec_module(self,module):
        p=Path(module.__spec__.origin);raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=pins[str(p.relative_to(root))]['sha256']:raise ValueError('parser_source_drift')
        exec(compile(raw,str(p),'exec'),module.__dict__)

def audit(event,args):
    if event.startswith('socket.') or event in ('sqlite3.connect','subprocess.Popen','os.system'):raise PermissionError('parser_external_operation')
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).absolute()
        if p.name.startswith('.env') or p.suffix in ('.db','.sqlite3','.sqlite'):raise PermissionError('parser_private_data')
        if p.is_relative_to(root) and str(p.relative_to(root)) not in pins:raise PermissionError('parser_unpinned_read')
        if args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT):raise PermissionError('parser_no_writes')

sys.addaudithook(audit);sys.meta_path.insert(0,Pinned())
from app.providers.kiwoom import KiwoomProvider
request=json.loads(sys.stdin.read());parser=KiwoomProvider(None)
if request.get('resolve'):
    class RecordedLists:
        def post(self,path,api,body):
            if path!='/api/us/stkinfo' or api!='usa10099':raise ValueError('unplanned_symbol_lookup')
            return request['lists'][body['stex_tp']]
    value=KiwoomProvider(RecordedLists()).resolve_us_symbol(request['resolve'], exchange=request.get('exchange'))
    print(json.dumps(dict(resolved=value.model_dump(mode='json') if value else None)))
    raise SystemExit(0)
spec=(parser._SPECS if request['market']=='kr' else parser._US_SPECS)[request['timeframe']]
rows=parser._find_rows(request.get('body',{}),spec[1]);parsed=[]
for row in rows:
    one=parser._normalize_rows([row],1)
    if len(one)!=1:raise ValueError('original_parser_dropped_row')
    parsed.extend(one)
print(json.dumps(dict(api=spec[0],rows=parsed,input_rows=len(rows),parser_sha256=pins['app/providers/kiwoom.py']['sha256'])))
