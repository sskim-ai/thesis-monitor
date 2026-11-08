"""Bounded offline original-code Source process. No model or auth operations."""
from pathlib import Path
import hashlib,json,os,sys
sys.dont_write_bytecode=True
config=json.loads(Path(sys.argv[1]).read_bytes());source=Path(config['source_root'])
sys.path.insert(0,str(source));os.environ['THESIS_MONITOR_ENV_FILE']=''
sha=lambda b:hashlib.sha256(b).hexdigest()
seen=set();reads=set();ready=False
def audit(event,args):
    if event.startswith('socket.') or event in ('sqlite3.connect','subprocess.Popen','os.system'):
        raise PermissionError('VERSIONED_SOURCE_NO_NETWORK_DB_OR_EXEC')
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0]))
        if p.name.startswith('.env') or p.name=='auth.json' or '.codex' in p.parts:
            raise PermissionError('VERSIONED_SOURCE_NO_CREDENTIALS')
        if len(args)>2 and isinstance(args[2],int) and args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):
            raise PermissionError('VERSIONED_SOURCE_READ_ONLY')
        if not ready and p.is_absolute():reads.add(str(p))
sys.addaudithook(audit)
from maintenance.c21g_analysis_source import restore_view
from app.services import vnext_unified_judgment as engine,vnext_balanced_stage_review as stages
from app.services.vnext_daily_research import UseRegistry
from app.services.vnext_optional_fy1_research import attach
from app.services.vnext_codex_research import numeric_catalog
from app.services.vnext_research_store import digest
packet=json.loads(Path(config['packet_path']).read_bytes())
assert digest(packet)==config['packet_sha256']
kwargs=dict(config['restore']);kwargs['packet']=packet
view,counts=restore_view(**kwargs)
registry=UseRegistry();ticker=packet['base']['public_security']['ticker']
def rebuild():
    economic=view.packet(ticker);economic['numeric_catalog']=numeric_catalog(economic);economic=attach(economic)
    actual=engine.build_bundle(economic,registry=registry,contract=engine.AI_OWNED_V3,valuation_analysis_owner=view)
    if actual!=packet:raise ValueError('ORIGINAL_SOURCE_VERSION_PACKET_NOT_EXACT')
    return actual,economic
actual,economic=rebuild()
closure={}
for module in tuple(sys.modules.values()):
    p=getattr(module,'__file__',None)
    if p and Path(p).is_relative_to(source):
        p=Path(p)
        if p.suffix!='.py':raise ValueError('SOURCE_CLOSURE_NOT_PYTHON')
        closure[str(p.relative_to(source))]=sha(p.read_bytes())
snapshot=json.loads(Path(config['snapshot_manifest']).read_bytes())
assert all(snapshot['source_files'].get(n)==pin for n,pin in closure.items())
for n,pin in packet['implementation'].items():
    rel='app/'+n if n=='vnext_worker.py' else 'app/services/'+n
    assert snapshot['source_files'][rel]==pin
inputs={}
for p in reads:
    path=Path(p)
    if path.is_file() and (any(path.is_relative_to(Path(root)) for root in config['data_roots']) or p in config['input_files']):inputs[p]=sha(path.read_bytes())
ready=True
identity=dict(commit=snapshot['commit'],loaded_closure_sha256=digest(closure),loaded_files=len(closure),packet_sha256=digest(packet),raw_receipt_inputs_sha256=digest(inputs),source_implementation=packet['implementation'])
schema=stages.output_schema(packet,stages.UNIFIED_AI_V3_SOL_HIGH)
request,prompt=stages._stage_request(invocation_id='C21Q_OFFLINE_NOT_MODEL',account='SYNTHETIC_ACCOUNT_NOT_TRANSPORT',packet=packet,stage='BLIND',version=stages.UNIFIED_AI_V3_SOL_HIGH,knowledge='',registry=registry,prior=None)
def verify():
    for n,pin in closure.items():
        if sha((source/n).read_bytes())!=pin:raise ValueError('ORIGINAL_CODE_DRIFT')
    for n,pin in inputs.items():
        if sha(Path(n).read_bytes())!=pin:raise ValueError('ORIGINAL_RAW_OR_RECEIPT_DRIFT')
def emit(v):print(json.dumps(v,ensure_ascii=False,separators=(',',':')),flush=True)
emit(dict(ready=True,original_packet_exact=True,packet_sha256=digest(actual),closure=closure,input_pins=inputs,producer_identity=identity,owner_counts=counts,old_high_request=request,old_high_prompt_sha256=digest(prompt.encode()),old_high_schema_sha256=digest(schema)))
for line in sys.stdin:
    try:
        message=json.loads(line)
        if message==dict(method='close'):emit(dict(closed=True));break
        if message!=dict(method='rebuild'):raise ValueError('RPC_METHOD_NOT_ALLOWED')
        verify();actual,economic=rebuild();verify()
        emit(dict(contract='VERSIONED_ORIGINAL_SOURCE_REPLAY_V1',packet=actual,economic=economic,schema=schema,producer_identity=identity,dated_only=True,current_source=False,original_owner_replayed=True))
    except Exception as e:emit(dict(error=type(e).__name__,reason=str(e)[:160]));break
