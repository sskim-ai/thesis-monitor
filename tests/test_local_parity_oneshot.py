"""Changed scheduled handoffs only; synthetic registration and no physical wire."""
import asyncio
from datetime import datetime
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
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from app.services.unified_live_source_transport import SourceSafetyStop
from tests.test_manual_source_budget import offline_only
from tests.test_local_launchd_entry import configuration, code_pin
from tests.test_native_settings_schema import schema, bridge, packet
from tests.test_native_env_path_parity import native


class BoundaryReached(RuntimeError):
    pass


def cycle_probe(folder, market, monkeypatch, *, mismatch=False):
    from app.config import Settings
    from app.services import codex_runtime_binding as binding
    from app.services import kiwoom_global_lane as lane
    from app.services import production_source_context as context
    from app.services import production_source_transport as transport
    from app.services import completed_price_state
    from app.services.canonical_source_acquisition import _acquire_all
    from app.services.production_source_configuration import ProductionSourceConfiguration
    from app.services.research_artifact_budget import active_budget
    from app.services.selected_source_plan import SelectedRequestPlan
    from tests.test_c22ab_selected_source import compile_market
    from tests.test_minimal_class_c_export import database
    from scripts.unified_stock_source_worker import sha
    import sqlite3

    folder.mkdir()
    path, raw = configuration(folder, market)
    permission = database(folder, [(t,m) for m in ('kr','us') for t in UNIVERSE[m]])
    with sqlite3.connect(permission.database) as db:
        for m in ('kr','us'):
            for index,ticker in enumerate(UNIVERSE[m]):
                column,value=('cik',str(10000+index)) if m=='us' else ('corp_code',str(10000000+index))
                db.execute('UPDATE securitymaster SET '+column+'=? WHERE ticker=?',(value,ticker))
                for table in ('securitymaster','watchlistitem','company'):
                    db.execute('UPDATE '+table+' SET company_name=? WHERE ticker=?',('Synthetic '+ticker,ticker))
                if m=='kr':db.execute("UPDATE securitymaster SET identity_provider='opendart' WHERE ticker=?",(ticker,))
    protocol=folder/'protocol.json';protocol.write_text('{}')
    item=dict(path=str(protocol),sha256=sha(protocol.read_bytes()),purpose='PUBLIC_PROTOCOL')
    source=ProductionSourceConfiguration(database_path=str(permission.database),native_owner_root=str(folder),
        native_python=sys.executable,completed_close=item,issuer_identity=item,
        kr_listing_routing=dict(item,purpose='IDENTITY_ROUTING_ONLY'),kis_protocols={'probe.json':item})
    documents={'source':source.model_dump(mode='json'),'binding':{},
        'endpoints':{p:[dict(host='offline.invalid',prefix='/',methods=['GET','POST'],endpoint='SYNTHETIC')]
            for p in job.LOCAL_CAPS[market]},
        'issuer':dict(compile_market('kr','000660')[1]['identities']['000660'],exchange='KRX')}
    for name,value in documents.items():
        p=folder/(name+'.json');p.write_text(json.dumps(value))
        key={'source':'source_configuration','binding':'model_binding','endpoints':'endpoint_rules','issuer':'auxiliary_issuer'}[name]
        raw[key]=dict(path=str(p),sha256=sha(p.read_bytes()),purpose='PROTOCOL_CONTROL')
    if market=='kr':raw.pop('auxiliary_issuer')
    config=job.LocalScheduleConfiguration.model_validate(raw)
    class OfflineSettings(Settings):
        def __init__(self,**kw):
            kw.pop('_env_file',None)
            super().__init__(_env_file=None,database_url='sqlite:///'+str(permission.database),**kw)
    monkeypatch.setattr('app.config.Settings',OfflineSettings)
    monkeypatch.setattr(binding,'binding_from_json',lambda v:SimpleNamespace(executable='SYNTHETIC'))
    monkeypatch.setattr(binding,'parent_environment',lambda v:{})
    monkeypatch.setattr(binding,'validate_binding',lambda *a,**kw:None)
    lock=folder/'lane.lock';lock.touch()
    monkeypatch.setattr(lane,'configured_lane',lambda:SimpleNamespace(_open=lambda:os.open(lock,os.O_RDONLY),_state=lambda:None))
    def seal(self,root,selected):
        (root/'static').mkdir(parents=True)
        (root/'static/official-security-identity.json').write_text('{}')
        (root/'static/kr-list-routing.json').write_text(json.dumps(dict(list=[dict(code=t,marketCode='0') for t in UNIVERSE['kr']])))
        return {}
    monkeypatch.setattr(ProductionSourceConfiguration,'seal_protocols',seal)
    seen={}
    def inspect(*a,**kw):
        seen['inspect_settings']=kw['settings']
        return dict(owner_head='b'*40,owner_files={'app/main.py':'b'*64},
            settings_sha256='c'*64,request_environment_sha256='d'*64)
    monkeypatch.setattr(context,'inspect_native',inspect)
    _,args,_=compile_market(market,UNIVERSE[market][0])
    credentials={p:['SYNTHETIC_NOT_A_KEY:'+p] for p in args['config_identities']}
    monkeypatch.setattr(context,'credential_binding',lambda *a:credentials)
    def boundary(*a,**kw):
        seen['boundary']=True
        raise BoundaryReached('BEFORE_ANY_PHYSICAL_HTTP')
    monkeypatch.setattr(completed_price_state,'require_plan',boundary)
    async def collect(self,**kw):
        seen.update(frozen=kw['frozen'],kis=kw['kis_plan'],budget=active_budget())
        assert self.native_settings is self.settings is seen['inspect_settings']
        if mismatch:kw['frozen']['optional_news_429']='ALTERED_POLICY'
        plan=SelectedRequestPlan.model_validate(kw['frozen']['plan'])
        dispatcher=SimpleNamespace(plan=plan,run_ledger=self.run_ledger)
        await _acquire_all(root=kw['root'],frozen=kw['frozen'],settings=self.settings,
            dispatcher=dispatcher,inner=None,policy=None,guard=lambda:None,native_settings=self.native_settings)
    monkeypatch.setattr(transport.NativeProductionSourceTransport,'collect',collect)
    monkeypatch.setattr(job,'load_adapter',lambda *a,**kw:pytest.fail('MODEL_NOT_REACHED'))
    from app.services.prospective_class_c_owner import completed_clock
    session=completed_clock(market,datetime.now(job.KST))['target']
    with pytest.raises(SourceSafetyStop if mismatch else BoundaryReached):
        asyncio.run(job._local_registered_cycle(config,folder,session))
    rows=[json.loads(line) for line in (folder/'campaign.jsonl').read_text().splitlines()]
    assert not any(r['event'].startswith('PHYSICAL_') for r in rows)
    seen['identity']=rows[0]['identity'];seen['rows']=rows
    seen['source_budget']=json.loads((folder/'source-time-budget.json').read_bytes())
    assert all(not v for v in credentials.values())
    return seen


def test_us_scheduled_caller_freeze_to_original_acquisition_gate(tmp_path,monkeypatch,offline_only):
    value=cycle_probe(tmp_path/'us','us',monkeypatch)
    assert value['boundary'] and value['budget'] is not None
    assert value['frozen']['optional_news_429']==value['identity']['runtime_cap']['optional_news_429']
    assert value['frozen']['us_selected_dated_sr']['enabled'] is True
    assert len(value['frozen']['plan']['subjects'])==14
    assert value['identity']['max_models']==42 and value['identity']['max_http']==710
    assert value['identity']['b2_retry_policy']=='B2_PER_TICKER_ONE_RETRY_V1' and value['source_budget']['ceiling_seconds']==1800


def test_kr_scheduled_caller_kis_flows_chart_and_original_600_budget(tmp_path,monkeypatch,offline_only):
    value=cycle_probe(tmp_path/'kr','kr',monkeypatch)
    assert value['boundary'] and value['budget'] is not None
    assert 'optional_news_429' not in value['frozen']
    assert value['frozen']['kr_stock_chart_v3'] is True
    assert len(value['frozen']['kr_stock_flow_reads'])==8 and value['kis'] is not None
    assert len(value['frozen']['plan']['subjects'])==8
    assert value['identity']['max_models']==18 and value['identity']['max_http']==332
    assert value['identity'].get('timeout_retry_cap',0)==0 and value['source_budget']['ceiling_seconds']==600


def test_policy_mismatch_still_stops_before_physical_wire(tmp_path,monkeypatch,offline_only):
    value=cycle_probe(tmp_path/'mismatch','us',monkeypatch,mismatch=True)
    assert not value.get('boundary')
    assert value['rows'][-1]['event']=='STOP'
    assert not any(r['event'].startswith(('PHYSICAL_','MODEL')) for r in value['rows'])


def test_both_native_inspect_and_actual_bridge_children_share_config(schema,monkeypatch):
    from app.services.production_source_context import inspect_native
    from app.services.production_source_transport import NativeProductionSourceTransport
    n=schema;original=n.env.read_bytes();owners=[]
    for market in ('us','kr'):
        folder=n.tmp/('inspect-'+market);folder.mkdir()
        owner=inspect_native(n.config,folder,settings_env_file=str(n.env),settings=n.settings)
        owners.append(owner)
        async def run():
            b=bridge(n,packet(n,owner),monkeypatch,'child-'+market)
            try:
                await b.command({'stocks':True})
                assert (await b.command({'replay-stocks':True}))['status']=='PASS'
            finally:await b.shutdown()
            assert b.exit_receipt['returncode']==0
        asyncio.run(run())
    assert owners[0]==owners[1] and n.env.read_bytes()==original
    assert NativeProductionSourceTransport(n.settings).native_settings is None


def test_one_shot_is_separate_and_date_wide_single_use(tmp_path,monkeypatch,offline_only):
    path,raw=configuration(tmp_path);code_pin(monkeypatch)
    old=tmp_path/'runs/us-2026-11-19';old.mkdir(parents=True)
    (old/'intent.json').write_text('OLD_INTENT');(old/'terminal.json').write_text('OLD_STOP')
    seen=[]
    async def cycle(config,directory,session,**kw):
        seen.append((directory,session,kw['one_shot_tag']))
        return dict(status='SYNTHETIC_NO_SEND',normal_messages_sent=False)
    monkeypatch.setattr(job,'_local_registered_cycle',cycle)
    at=datetime.fromisoformat('2026-11-20T08:10:00+09:00')
    first=asyncio.run(job.run_local_scheduled(path,'us',now=at,one_shot_tag='us-20261120-deadbeef'))
    assert first['status']=='SYNTHETIC_NO_SEND'
    assert seen[0][0]==tmp_path/'runs/one-shot/2026-11-20/us-20261120-deadbeef'
    for tag in ('us-20261120-deadbeef','us-20261120-feedface'):
        assert asyncio.run(job.run_local_scheduled(path,'us',now=at,one_shot_tag=tag))['status']=='NO_RUN'
    assert len(seen)==1 and (old/'intent.json').read_text()=='OLD_INTENT' and (old/'terminal.json').read_text()=='OLD_STOP'


def test_one_shot_wrong_date_lock_failure_and_cancel_are_consumed(tmp_path,monkeypatch,offline_only):
    code_pin(monkeypatch)
    at=datetime.fromisoformat('2026-11-20T08:10:00+09:00')
    for kind in ('failure','cancel','lock','date'):
        folder=tmp_path/kind;path,_=configuration(folder);calls=[]
        async def cycle(*a,**kw):
            calls.append(True)
            if kind=='cancel':raise asyncio.CancelledError()
            raise RuntimeError('SYNTHETIC_SECRET_NOT_IN_TERMINAL')
        monkeypatch.setattr(job,'_local_registered_cycle',cycle)
        options=dict(now=at,one_shot_tag='us-20261120-deadbeef')
        if kind=='date':
            options['now']=datetime.fromisoformat('2027-11-20T08:10:00+09:00')
            assert asyncio.run(job.run_local_scheduled(path,'us',**options))['reason']=='ONE_SHOT_DATE_CLOSED'
        elif kind=='lock':
            with (folder/'pair.lease').open() as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                assert asyncio.run(job.run_local_scheduled(path,'us',**options))['reason'].endswith('LOCK_BUSY')
        else:
            with pytest.raises((RuntimeError,asyncio.CancelledError)):
                asyncio.run(job.run_local_scheduled(path,'us',**options))
            result=asyncio.run(job.run_local_scheduled(path,'us',**options));assert result['status']=='NO_RUN'
            terminal=next((folder/'runs/one-shot').rglob('terminal.json'))
            assert 'SYNTHETIC_SECRET' not in terminal.read_text() and len(calls)==1
        if kind in ('date','lock'):assert not calls
    with pytest.raises(ValueError,match='tag_scope'):
        asyncio.run(job.run_local_scheduled(path,'us',now=at,one_shot_tag='../invalid'))


def test_schedules_profiles_render_guards_and_protected_modules_are_unchanged():
    root=Path(__file__).resolve().parents[1]
    for market,hour,minute,days in (('us',6,10,range(2,7)),('kr',15,35,range(1,6))):
        p=plistlib.loads((root/'docs/operations/LOCAL_LAUNCHD_PLIST'/(market+'.plist')).read_bytes())
        assert p['StartCalendarInterval']==[dict(Weekday=d,Hour=hour,Minute=minute) for d in days]
        assert p['RunAtLoad'] is False and p['KeepAlive'] is False
    for name in ('app/services/research_no_send_run.py','app/services/model_execution_plan.py',
        'app/services/production_model_transport.py','app/services/us_dated_source_sr.py',
        'app/services/production_kis_sources.py','app/services/kr_stock_flow_source.py'):
        assert (root/name).read_bytes()==subprocess.check_output(['/usr/bin/git','show','568a1ffb:'+name],cwd=root)
    from app.services.vnext_execution_profile import SOL_HIGH_V1
    assert SOL_HIGH_V1.model=='gpt-6.1-sol' and SOL_HIGH_V1.effort=='high'
