"""Offline local scheduling boundaries; never live Source/model qualification."""
import asyncio
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.jobs import unified_market_snapshot as job
from app.services import prospective_class_c_owner as registration
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from tests.test_manual_source_budget import offline_only


def configuration(folder, market='us', enabled=True):
    folder.mkdir(parents=True, exist_ok=True)
    descriptor = dict(path=str(folder/'unused.json'), sha256='0'*64, purpose='PROTOCOL_CONTROL')
    value = dict(market=market, enabled=enabled, code_commit='a'*40, run_root=str(folder/'runs'),
        settings_env_file=str(folder/'unused.env'), shared_lease_path=str(folder/'pair.lease'),
        source_configuration=descriptor, model_binding=descriptor, endpoint_rules=descriptor)
    path = folder/'local.json'
    path.write_text(json.dumps(value))
    path.chmod(0o600)
    (folder/'pair.lease').touch()
    return path, value


def code_pin(monkeypatch):
    monkeypatch.setattr(job.subprocess, 'check_output', lambda args, **kw:
        'a'*40+'\n' if args[-2:] == ['rev-parse', 'HEAD'] else '')


def test_default_off_exact_scope_and_secret_safe_configuration(tmp_path, monkeypatch):
    path, value = configuration(tmp_path, enabled=False)
    monkeypatch.setattr(job, '_local_registered_cycle', lambda *a: pytest.fail('disabled_must_not_start'))
    assert asyncio.run(job.run_local_scheduled(path, 'us'))['status'] == 'DISABLED'
    for change in ({'mode':'SEND'}, {'market':'kr'}, {'owner':{}}, {'enabled':'true'}):
        path.write_text(json.dumps(dict(value, **change)))
        with pytest.raises(ValueError):
            asyncio.run(job.run_local_scheduled(path, 'us'))
    path.write_text(json.dumps(value))
    path.chmod(0o644)
    with pytest.raises(ValueError, match='operator_private'):
        job.read_local_configuration(path, 'us')


def test_calendar_closed_incomplete_dst_and_no_previous_day_fallback(tmp_path, monkeypatch):
    from app.services.unified_market_run import target_session
    path, _ = configuration(tmp_path)
    monkeypatch.setattr(job, '_local_registered_cycle', lambda *a: pytest.fail('closed_must_not_start'))
    for stamp in ('2026-11-27T06:10:00+09:00', '2026-11-23T06:10:00+09:00',
                  '2026-11-20T05:50:00+09:00'):
        assert asyncio.run(job.run_local_scheduled(path, 'us', now=datetime.fromisoformat(stamp)))['status'] == 'NO_RUN'
    assert str(target_session('us', datetime.fromisoformat('2026-03-06T06:10:00+09:00'))) == '2026-03-05'
    assert str(target_session('us', datetime.fromisoformat('2026-03-10T06:10:00+09:00'))) == '2026-03-09'
    assert str(target_session('us', datetime.fromisoformat('2026-11-21T06:10:00+09:00'))) == '2026-11-20'
    assert target_session('kr', datetime.fromisoformat('2026-11-19T15:20:00+09:00')) is None
    assert target_session('kr', datetime.fromisoformat('2026-11-21T15:35:00+09:00')) is None


def test_same_session_lock_intent_terminal_stop_and_failure_are_not_retried(tmp_path, monkeypatch):
    code_pin(monkeypatch)
    now = datetime.fromisoformat('2026-11-20T06:10:00+09:00')
    for state in ('intent.json', 'terminal.json', 'campaign.jsonl', 'STOP', 'failure', 'interrupt', 'success', 'lock'):
        folder = tmp_path/state
        path, _ = configuration(folder)
        directory = folder/'runs/us-2026-11-19'
        directory.mkdir(parents=True)
        calls = []
        async def cycle(*args):
            calls.append(True)
            if state == 'failure':
                raise RuntimeError('synthetic_secret_must_not_be_logged')
            if state == 'interrupt':
                raise asyncio.CancelledError()
            return dict(status='RENDER_VERIFIED_NO_SEND', normal_messages_sent=False)
        monkeypatch.setattr(job, '_local_registered_cycle', cycle)
        if state in ('intent.json', 'terminal.json', 'campaign.jsonl', 'STOP'):
            (directory/state).write_text('immutable evidence')
        if state in ('failure', 'interrupt'):
            with pytest.raises((RuntimeError, asyncio.CancelledError)):
                asyncio.run(job.run_local_scheduled(path, 'us', now=now))
            assert 'synthetic_secret' not in (directory/'terminal.json').read_text()
        elif state == 'success':
            assert asyncio.run(job.run_local_scheduled(path, 'us', now=now))['status'] == 'RENDER_VERIFIED_NO_SEND'
        elif state == 'lock':
            with (folder/'pair.lease').open('r') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                assert asyncio.run(job.run_local_scheduled(path, 'us', now=now))['reason'].endswith('LOCK_BUSY')
            assert not (directory/'intent.json').exists()
            continue
        assert asyncio.run(job.run_local_scheduled(path, 'us', now=now))['reason'] == 'SESSION_ALREADY_CONSUMED'
        assert len(calls) == (1 if state in ('failure', 'interrupt', 'success') else 0)


class CollectorReached(RuntimeError):
    pass


def original_cycle_probe(folder, market, monkeypatch):
    from app.config import Settings
    from app.services import codex_runtime_binding as binding
    from app.services import kiwoom_global_lane as lane_module
    from app.services import production_source_context as context
    from app.services import production_source_transport as transport
    from app.services.production_source_configuration import ProductionSourceConfiguration
    from tests.test_c22ab_selected_source import compile_market
    from tests.test_minimal_class_c_export import database

    path, config = configuration(folder, market)
    permission = database(folder, [(t,m) for m in ('kr','us') for t in UNIVERSE[m]])
    import sqlite3
    with sqlite3.connect(permission.database) as db:
        for m in ('kr','us'):
            for i,ticker in enumerate(UNIVERSE[m]):
                column, value = ('cik',str(10000+i)) if m == 'us' else ('corp_code',str(10000000+i))
                db.execute('UPDATE securitymaster SET '+column+'=? WHERE ticker=?',(value,ticker))
                for table in ('securitymaster','watchlistitem','company'):
                    db.execute('UPDATE '+table+' SET company_name=? WHERE ticker=?',('Synthetic '+ticker,ticker))
                if m == 'kr':
                    db.execute("UPDATE securitymaster SET identity_provider='opendart' WHERE ticker=?",(ticker,))
    protocol = folder/'protocol.json'
    protocol.write_text('{}')
    item = dict(path=str(protocol), sha256=digest({}), purpose='PUBLIC_PROTOCOL')
    # Config hash is over exact bytes, not canonical JSON: {} has no newline.
    import hashlib
    item['sha256'] = hashlib.sha256(protocol.read_bytes()).hexdigest()
    source_config = ProductionSourceConfiguration(database_path=str(permission.database), native_owner_root=str(folder),
        native_python=str(folder/'python'), completed_close=item, issuer_identity=item,
        kr_listing_routing=dict(item,purpose='IDENTITY_ROUTING_ONLY'), kis_protocols={'probe.json':item})
    documents = {'source':source_config.model_dump(mode='json'), 'binding':{},
        'endpoints':{p:[dict(host='offline.invalid',prefix='/',methods=['GET','POST'],endpoint='OFFLINE')]
            for p in job.LOCAL_CAPS[market]},
        'issuer':dict(compile_market('kr','000660')[1]['identities']['000660'], exchange='KRX')}
    for name, value in documents.items():
        p = folder/(name+'.json')
        p.write_text(json.dumps(value))
        key = {'source':'source_configuration', 'binding':'model_binding',
            'endpoints':'endpoint_rules', 'issuer':'auxiliary_issuer'}[name]
        config[key] = dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),purpose='PROTOCOL_CONTROL')
    if market == 'kr':
        config.pop('auxiliary_issuer')
    config = job.LocalScheduleConfiguration.model_validate(config)
    class OfflineSettings(Settings):
        def __init__(self, **kw):
            kw.pop('_env_file', None)
            super().__init__(_env_file=None, database_url='sqlite:///'+str(permission.database), **kw)
    monkeypatch.setattr('app.config.Settings', OfflineSettings)
    monkeypatch.setattr(binding, 'binding_from_json', lambda v:SimpleNamespace(executable='OFFLINE'))
    monkeypatch.setattr(binding, 'parent_environment', lambda v:{})
    monkeypatch.setattr(binding, 'validate_binding', lambda *a,**k:None)
    lock = folder/'lane.lock'
    lock.touch()
    monkeypatch.setattr(lane_module,'configured_lane',lambda:SimpleNamespace(
        _open=lambda:os.open(lock,os.O_RDONLY), _state=lambda:dict(halted=False,in_flight=False)))
    def seal(self, root, selected):
        (root/'static').mkdir(parents=True)
        (root/'static/official-security-identity.json').write_text('{}')
        (root/'static/kr-list-routing.json').write_text(json.dumps(dict(list=[dict(code=t,marketCode='0') for t in UNIVERSE['kr']])))
        return {'probe':dict(sha256='0'*64,purpose='SYNTHETIC_PROTOCOL_ONLY')}
    monkeypatch.setattr(ProductionSourceConfiguration,'seal_protocols',seal)
    monkeypatch.setattr(context, 'inspect_native', lambda *a:dict(owner_head='b'*40,
        owner_files={'app/main.py':'b'*64},settings_sha256='c'*64,request_environment_sha256='d'*64))
    _, args, _ = compile_market(market, UNIVERSE[market][0])
    credentials = {p:['NOT_A_CREDENTIAL:'+p] for p in args['config_identities']}
    monkeypatch.setattr(context,'credential_binding',lambda *a:credentials)
    observed = {}
    async def stop_before_wire(self, **kw):
        observed['collector'] = True
        raise CollectorReached('OFFLINE_ONLY_BEFORE_ANY_PHYSICAL_HTTP')
    monkeypatch.setattr(transport.NativeProductionSourceTransport,'collect',stop_before_wire)
    monkeypatch.setattr(job,'load_adapter',lambda *a,**kw:pytest.fail('model_factory_not_reached'))
    session = registration.completed_clock(market, datetime.now(timezone.utc))['target']
    with pytest.raises(CollectorReached):
        asyncio.run(job._local_registered_cycle(config, folder, session))
    budget = json.loads((folder/'source-time-budget.json').read_bytes())
    rows = [json.loads(line) for line in (folder/'campaign.jsonl').read_bytes().splitlines()]
    assert observed['collector'] and any(r['event']=='PLAN' for r in rows)
    identity = rows[0]['identity']
    assert identity['max_models'] == (30 if market == 'us' else 18)
    assert identity['max_http'] == (710 if market == 'us' else 332)
    assert identity.get('timeout_retry_cap',0) == (1 if market=='us' else 0)
    assert budget['ceiling_seconds'] == (1800 if market=='us' else 600)
    assert not any(r['event'].startswith('PHYSICAL_') for r in rows)
    assert all(not values for values in credentials.values())
    assert 'selected private' not in (folder/'source/production-frozen-source-plan.json').read_text()
    return dict(original_owner_plan_to_collector=True, market=market,
        approval_sha256=identity['approval_sha256'], database='SYNTHETIC_ONLY', source_seconds=budget['ceiling_seconds'],
        financial_HTTP=0, models=0)


def test_original_owner_ledger_freeze_and_registered_entry_in_new_processes(tmp_path):
    # Fresh interpreters exercise the real issuers; no serialized approval handles.
    results = []
    for market in ('us','us','kr'):
        folder = tmp_path/str(len(results))
        script = ('from pathlib import Path;import json,sys;from pytest import MonkeyPatch;'
            'from tests.test_local_launchd_entry import original_cycle_probe;'
            'from tests.test_manual_source_budget import offline_only;'
            'm=MonkeyPatch();p=Path(sys.argv[1]);p.mkdir();'
            'offline_only.__wrapped__(m,p);'
            'v=original_cycle_probe(p,sys.argv[2],m);'
            'print(json.dumps(v));m.undo()')
        process = subprocess.run([sys.executable,'-B','-c',script,str(folder),market],
            capture_output=True,text=True,timeout=90)
        assert process.returncode == 0, process.stderr
        results.append(json.loads(process.stdout.splitlines()[-1]))
    assert len({r['approval_sha256'] for r in results}) == 3
    assert all(r['original_owner_plan_to_collector'] and r['financial_HTTP']==r['models']==0 for r in results)


def test_market_terminal_recorded_before_original_child_closes(monkeypatch):
    from app.services.production_source_backend import CanonicalProductionSourceBackend
    events=[]
    ledger=SimpleNamespace(bind_model_plan=lambda c:events.append('bind'),
        rendered_market=lambda c,r:events.append('terminal'))
    child=SimpleNamespace(verify=lambda:None,market='us',binding=lambda:{},
        plan=SimpleNamespace(sha256='0'*64,cohort=SimpleNamespace(cutoff='2026-11-20T06:10:00+09:00')),
        owner=SimpleNamespace(close=lambda:events.append('close')))
    async def prepare(**kw):return child,{}
    async def run(*args):return dict(status='RENDER_VERIFIED_NO_SEND')
    monkeypatch.setattr(CanonicalProductionSourceBackend,'prepare_registered',prepare)
    monkeypatch.setattr(job,'load_adapter',lambda *a,**kw:object())
    monkeypatch.setattr(job,'build_engine',lambda *a,**kw:SimpleNamespace(run=run))
    source=dict(run_ledger=ledger,frozen={'stock_plan':{'implementation_sha':'a'*40}})
    asyncio.run(job.run_registered(None,source=source,model={'run_ledger':ledger},
        mode='LIVE_NO_SEND',record_market_terminal=True))
    assert events == ['bind','terminal','close']


def test_plist_absolute_single_entry_no_credentials_no_auto_restart():
    folder=Path(__file__).resolve().parents[1]/'docs/operations/LOCAL_LAUNCHD_PLIST'
    for market,hour,minute in (('us',6,10),('kr',15,35)):
        value=plistlib.loads((folder/(market+'.plist')).read_bytes())
        assert value['RunAtLoad'] is False and value['KeepAlive'] is False
        assert value['ProgramArguments'][1:5] == ['-B','-m','app.jobs.unified_market_snapshot','--local-scheduled']
        assert value['ProgramArguments'][-2:] == ['--market',market]
        for key in ('WorkingDirectory','StandardOutPath','StandardErrorPath'):
            assert Path(value[key]).is_absolute()
        assert Path(value['ProgramArguments'][0]).is_absolute()
        weekdays = range(2,7) if market == 'us' else range(1,6)
        assert value['StartCalendarInterval'] == [dict(Weekday=d,Hour=hour,Minute=minute) for d in weekdays]
        assert not value.get('EnvironmentVariables')
        assert 'monitor_daily' not in value['Label']
