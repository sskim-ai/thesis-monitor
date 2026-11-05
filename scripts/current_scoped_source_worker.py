"""Pinned original provider code over a private parent-owned HTTP channel.

This worker owns no network or registration authority. Private protocol lines
are never execution logs. Original capture and replay functions remain intact.
"""
import base64
import contextlib
import ctypes
import hashlib
import importlib.abc
import importlib.util
import json
import logging
import os
from pathlib import Path
import socket
import sys
from types import SimpleNamespace

frozen_path, expected = sys.argv[1:]
raw = Path(frozen_path).read_bytes()
assert hashlib.sha256(raw).hexdigest() == expected
frozen = json.loads(raw)
stage, output = Path(frozen['stage']), Path(frozen['output'])
site = '/Users/sskim/Codex/thesis-monitor/.venv/lib/python3.11/site-packages'
sys.path[:0] = [str(stage), site]
os.environ.update(THESIS_MONITOR_ENV_FILE='', DATABASE_URL='sqlite://', HOME=str(output),
    TMPDIR=str(output), ENABLE_LIVE_PROVIDERS='false', NOTIFICATION_DRY_RUN='true')
logging.disable(logging.CRITICAL)
from scripts import unified_stock_source_worker as stock_worker
from app.services.native_completed_market import select_completed_daily_rows
from app.services.completed_session_projection import project_completed_rows
from app.services.query_time_monitoring_price import project_monitoring_rows
from app.services.short_history_reference import review_rows as review_short_rows
from app.services.scoped_source_plan import ScopedStockRead
from app.services.scoped_external_code_manifest import validate_external_manifest, CONTRACT_V2
from datetime import datetime as SourceDateTime
import httpx


def no_network(*args, **kwargs):
    raise PermissionError('SCOPED_WORKER_NO_NETWORK')


socket.socket.connect = socket.socket.connect_ex = socket.getaddrinfo = no_network
owner_root = Path(frozen['external_root'])
pins = frozen['external_pins']
validate_external_manifest(pins, frozen.get('external_code_contract'))


class PinnedLoader(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, fullname, path=None, target=None):
        if fullname != 'app' and not fullname.startswith('app.'):
            return None
        stem = fullname.replace('.', '/')
        options = [stem+'.py', stem+'/__init__.py']
        names = [n for n in options if n in pins]
        if len(names) != 1:
            raise PermissionError('UNAPPROVED_EXTERNAL_CODE_DEPENDENCY')
        name = names[0]
        return importlib.util.spec_from_file_location(fullname, owner_root/name,
            loader=self, submodule_search_locations=[] if name.endswith('/__init__.py') else None)

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        path = Path(module.__spec__.origin)
        rel = str(path.relative_to(owner_root))
        if (frozen.get('external_code_contract') == CONTRACT_V2
                and any(p.is_symlink() for p in (path, *path.parents))):
            raise PermissionError('EXTERNAL_CODE_SIZE_OR_PATH_CHANGED')
        source = path.read_bytes()
        assert hashlib.sha256(source).hexdigest() == pins[rel]['sha256']
        if frozen.get('external_code_contract') == CONTRACT_V2:
            if len(source) != pins[rel]['bytes']:
                raise PermissionError('EXTERNAL_CODE_SIZE_OR_PATH_CHANGED')
        exec(compile(source, str(path), 'exec'), module.__dict__)


def audit(event, args):
    if event.startswith('socket.') or event in ('sqlite3.connect','subprocess.Popen','os.system'):
        raise PermissionError('WORKER_EXTERNAL_OPERATION_DENIED')
    if event == 'open' and not isinstance(args[0], int):
        path = Path(os.path.abspath(os.fsdecode(args[0])))
        if path.is_relative_to(owner_root) and str(path.relative_to(owner_root)) not in pins:
            raise PermissionError('WORKER_EXTERNAL_FILE_NOT_PINNED')
        if any(p.startswith('.env') for p in path.parts) or path.suffix in ('.db','.sqlite','.sqlite3'):
            raise PermissionError('WORKER_PRIVATE_CONTENT_DENIED')
        write=bool(args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if write:
            if not path.is_relative_to(output):
                raise PermissionError('WORKER_WRITE_OUTSIDE_CAPTURE')
        elif not (path.is_relative_to(output) or str(path) in frozen['read_paths']
                or any(path.is_relative_to(Path(r)) for r in (site,
                    '/opt/homebrew/Cellar/python@3.11/3.11.15_3','/usr/share/zoneinfo','/usr/share/locale'))
                or str(path) in ('/etc/localtime','/private/etc/localtime','/dev/null','/dev/urandom')):
            raise PermissionError('WORKER_UNDECLARED_CONTENT_READ')


sys.addaudithook(audit)
for key in list(sys.modules):
    if key == 'app' or key.startswith('app.'):
        del sys.modules[key]
sys.meta_path.insert(0, PinnedLoader())
from app.config import Settings
from app.providers import kiwoom as owner
from app.services.ohlcv_service import OhlcvService
from app.services.symbol_resolver import SymbolResolver

channel = sys.stdout


def emit(value):
    channel.write(json.dumps(value, ensure_ascii=False)+'\n')
    channel.flush()


# Query the actual kernel policy, not the presence of a launcher flag.
sandbox = ctypes.CDLL('/usr/lib/libsandbox.dylib')
sandbox.sandbox_check.restype = ctypes.c_int
denials = {op: sandbox.sandbox_check(os.getpid(), op.encode(), 0) != 0
    for op in ('network-outbound', 'network-inbound')}
denials.update({label: sandbox.sandbox_check(os.getpid(), op.encode(), 1, path.encode()) != 0
    for label, op, path in (
        ('other_home', 'file-read-data', str(output.parent/'not-granted/home.txt')),
        ('other_database', 'file-read-data', str(output.parent/'not-granted/test.sqlite3')),
        ('arbitrary_exec', 'process-exec', '/usr/bin/true'))})
if not all(denials.values()):
    raise PermissionError('SCOPED_WORKER_OS_BOUNDARY_NOT_EFFECTIVE')
from app.services.kiwoom_global_lane import configured_lane
if configured_lane() is not None:
    raise PermissionError('SCOPED_WORKER_CHILD_LANE_FORBIDDEN')
secret = json.loads(sys.stdin.readline())
settings = Settings(_env_file=None, KIWOOM_APP_KEY=secret['app_key'],
    KIWOOM_SECRET_KEY=secret['secret_key'], KIWOOM_BASE_URL_REAL='https://api.kiwoom.com',
    KIWOOM_MAX_RETRIES=0, KIWOOM_TIMEOUT_SECONDS=60,
    KIWOOM_REQUEST_INTERVAL_SECONDS=max(.2, frozen['request_interval']),
    SECTOR_MAP_PATH=output/'unused-sector-map.csv')
del secret
assert settings.kiwoom_base_url=='https://api.kiwoom.com'
assert settings.kiwoom_env=='real' and settings.kiwoom_max_retries==0
assert settings.kiwoom_app_key and settings.kiwoom_secret_key
assert settings.kiwoom_timeout_seconds==60 and settings.kiwoom_request_interval_seconds>=.2
emit({'attestation':dict(base_url=settings.kiwoom_base_url,environment=settings.kiwoom_env,
    retries=settings.kiwoom_max_retries,timeout=settings.kiwoom_timeout_seconds,
    interval=settings.kiwoom_request_interval_seconds,credential_values_exported=False,
    os_policy_denials=denials,child_global_lane=False,worker_pid=os.getpid(),worker_uid=os.getuid(),
    original_settings_class=True,external_env_read=False)})


def post(url, *, json, headers, timeout):
    request = httpx.Request('POST',url,json=json,headers=headers)
    emit({'wire':dict(method=request.method,url=str(request.url),headers=list(request.headers.multi_items()),
        body_b64=base64.b64encode(request.content).decode())})
    line = sys.stdin.readline()
    if not line:
        raise PermissionError('PARENT_DISCONNECTED')
    data = __import__('json').loads(line)
    if set(data) != {'response'}:
        raise PermissionError('PARENT_RESPONSE_REQUIRED')
    response=data['response']
    if response.get('error'):
        raise httpx.TransportError('PARENT_SEALED_REQUEST_DENIED')
    return httpx.Response(response['status'],content=base64.b64decode(response['body_b64'],validate=True),
        headers=response['headers'],request=request)


owner.httpx = SimpleNamespace(post=post, HTTPError=httpx.HTTPError)


class CompletedMarketProvider(owner.KiwoomProvider):
    def _normalize_rows(self, rows, count):
        normalized = super()._normalize_rows(rows,max(count,len(rows)))
        return select_completed_daily_rows(normalized,
            target_session=frozen['latest_completed_us_session'],count=count)


service=OhlcvService(SymbolResolver(settings.sector_map_path),
    CompletedMarketProvider(owner.KiwoomClient(settings,owner.KiwoomAuth(settings))))


class Client:
    def __enter__(self): return self
    def __exit__(self,*unused): return False
    def post(self,*args,**kwargs): return post(*args,**kwargs)


class Progress:
    def write(self,text):
        if text.strip(): emit({'progress':json.loads(text)})
    def flush(self): pass


done=set()
pending_handoff=frozen.get('pending_handoff')
pending_ready=pending_handoff is None
source_root = Path(frozen.get('historical_source_root', str(output/'stocks')))
for line in sys.stdin:
    command=json.loads(line)
    if command == {'close':True}: break
    try:
        if set(command)=={'pending_handoff'} and pending_handoff is not None and not pending_ready:
            action=command['pending_handoff']
            expected_keys=set(pending_handoff)|{'nonce'}
            if (set(action)!=expected_keys or {k:v for k,v in action.items() if k!='nonce'}!=pending_handoff
                    or pending_handoff.get('scope')!='SCOPED_SOURCE_ONLY_PENDING'
                    or pending_handoff.get('generation_id')!=frozen['stock_plan']['run_id']
                    or not isinstance(action['nonce'],str) or len(action['nonce'])!=64):
                raise PermissionError('PENDING_WORKER_HANDOFF_DENIED')
            emit({'pending_ack':dict(**pending_handoff,nonce_sha256=stock_worker.sha(stock_worker.encoded(action['nonce'])),worker_pid=os.getpid())})
            pending_ready=True
            continue
        if not pending_ready:raise PermissionError('PENDING_WORKER_HANDOFF_REQUIRED')
        if (set(command) in ({'projection'}, {'short_reference'}, {'monitoring'})
                and (next(iter(command)),next(iter(command.values()))) not in done):
            kind=next(iter(command))
            entry = next(r for r in frozen['stock_plan']['reads'] if r['entry_id']==command[kind])
            ordinal = frozen['stock_plan']['reads'].index(entry)+1
            receipt = json.loads((source_root/f'role-{ordinal:03d}.receipt.json').read_bytes())
            if (receipt['entry'] != entry or receipt['status']!='CAPTURED'
                    or receipt['run_id']!=frozen['stock_plan']['run_id']
                    or receipt['acquisition_id']!=frozen['stock_plan']['acquisition_id']
                    or receipt['plan_sha256']!=stock_worker.sha(stock_worker.encoded(frozen['stock_plan']))):
                raise ValueError('projection_original_receipt_mismatch')
            parser=owner.KiwoomProvider(None)
            specs=parser._SPECS if entry['market']=='kr' else parser._US_SPECS
            api,keys=specs[entry['timeframe']]
            if api!=entry['api_id']: raise ValueError('projection_original_parser_api')
            all_rows=[]
            source_pages=[]
            cursors=set()
            previous={'cont_yn':'N','next_key':''}
            for number,page in enumerate(receipt['pages'],1):
                if page['page_ordinal']!=number or page['request']['continuation']!=previous:
                    raise ValueError('projection_page_chain_mismatch')
                cursor=previous['next_key']
                if cursor in cursors: raise ValueError('projection_cursor_repeated')
                cursors.add(cursor)
                relative=Path(page['artifact'])
                if relative.is_absolute() or '..' in relative.parts:
                    raise ValueError('projection_source_path_escape')
                path=source_root/relative
                if any(p.is_symlink() for p in (path,*path.parents)):
                    raise ValueError('projection_source_symlink')
                raw=path.read_bytes()
                if hashlib.sha256(raw).hexdigest()!=page['source_sha256']:
                    raise ValueError('projection_raw_hash_mismatch')
                body=json.loads(raw)
                rows=parser._find_rows(body,keys)
                for row in rows:
                    parsed=parser._normalize_rows([row],1)
                    if len(parsed)!=1: raise ValueError('projection_original_parser_dropped_row')
                    all_rows.extend(parsed)
                source_pages.append(dict(page=number,sha256=page['source_sha256'],rows=len(rows)))
                previous=page['response_continuation']
            if kind=='projection':
                selected,proof=project_completed_rows(all_rows,read=ScopedStockRead.model_validate(entry),
                    cutoff=SourceDateTime.fromisoformat(frozen['stock_plan']['frozen_at']),source_pages=source_pages)
                artifact=f'projection-{ordinal:03d}.json'
                status='COMPLETED_PROJECTION_REPLAY_PASS'
            elif kind=='monitoring':
                proof=project_monitoring_rows(all_rows,read=ScopedStockRead.model_validate(entry),
                    frozen_at=SourceDateTime.fromisoformat(frozen['stock_plan']['frozen_at']),
                    observed_at=SourceDateTime.fromisoformat(receipt['completed_at']),source_pages=source_pages)
                selected=proof['rows']
                artifact=f'monitoring-{ordinal:03d}.json'
                status='QUERY_TIME_SNAPSHOT_REPLAY_PASS'
            else:
                selected,proof=review_short_rows(all_rows=all_rows,read=ScopedStockRead.model_validate(entry),
                    cutoff=SourceDateTime.fromisoformat(frozen['stock_plan']['frozen_at']),source_pages=source_pages,
                    source_receipt=receipt)
                artifact=f'short-reference-{ordinal:03d}.json'
                status='SHORT_REFERENCE_REPLAY_PASS'
            body=dict(rows=selected,all_rows=all_rows,receipt=proof,parser_pins=pins)
            data=stock_worker.encoded(body)
            stock_worker.save(output/artifact,data)
            done.add((kind,command[kind]))
            result=dict(status=status,entry_id=entry['entry_id'],
                artifact=artifact,sha256=hashlib.sha256(data).hexdigest())
        elif command == {'stocks':True} and 'stocks' not in done and 'historical_source_root' not in frozen:
            done.add('stocks')
            stock_worker.httpx=SimpleNamespace(Client=lambda **kw:Client(),HTTPTransport=lambda **kw:None,HTTPError=httpx.HTTPError)
            with contextlib.redirect_stdout(Progress()):
                stock_worker.acquire(frozen['stock_plan'],output/'stocks',owner,settings)
            owner.httpx=SimpleNamespace(post=post,HTTPError=httpx.HTTPError)
            result=dict(status='CAPTURE_COMPLETE_NOT_QUALIFIED')
        elif set(command)=={'replay'} and command['replay'] in (1,2) and 'stocks' in done and ('replay',command['replay']) not in done:
            done.add(('replay',command['replay']))
            original_datetime=owner.datetime
            original_write=stock_worker.write
            try:
                def replay_write(path,value):
                    if path != output/'raw-owner-replay.json':
                        raise PermissionError('UNEXPECTED_REPLAY_WRITE')
                    return original_write(output/f'raw-owner-replay-{command["replay"]}.json',value)
                stock_worker.write=replay_write
                stock_worker.replay(frozen['stock_plan'],output/'stocks',owner)
            finally:
                owner.datetime=original_datetime
                stock_worker.write=original_write
                owner.httpx=SimpleNamespace(post=post,HTTPError=httpx.HTTPError)
            data=(output/f'raw-owner-replay-{command["replay"]}.json').read_bytes()
            result=dict(status='REPLAY_RESULT',rows=json.loads(data),sha256=hashlib.sha256(data).hexdigest())
        elif command=={'discovery':True} and 'discovery' not in done:
            done.add('discovery')
            for exchange in ('ND','NY','NA'): service.provider._get_us_stock_list(exchange)
            result=dict(status='DISCOVERY_CAPTURE_COMPLETE_NOT_QUALIFIED')
        elif set(command)=={'market'} and command['market'] in frozen['us_market_symbols'] and command['market'] not in done:
            if 'discovery' not in done: raise ValueError('DISCOVERY_REQUIRED')
            done.add(command['market'])
            value=service.get_ohlcv(symbol=command['market'],market='US',periods=['daily'],count=2,
                include_indicators=False,indicator_limit=0,adjusted=True,include_investor_flows=False)
            result=dict(status=200,body=value.model_dump(mode='json'))
        else:
            raise ValueError('UNPLANNED_WORKER_COMMAND')
    except Exception as exc:
        result=dict(status='OWNER_REJECTED',error_type=type(exc).__name__,exception_text_withheld=True)
    emit({'result':result})
