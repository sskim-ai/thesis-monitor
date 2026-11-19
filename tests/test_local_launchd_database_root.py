"""DB-root parity only: empty test files/stat, no real Owner, DB or dispatch."""
import ast
import asyncio
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from app.jobs import unified_market_snapshot as job
from app.services.selected_source_registration import database_target
from tests.test_manual_source_budget import offline_only

BASE='7fa4b9d2dea654da097b44a0b02d0d13868ac393'


class CaptureReached(RuntimeError):
    pass


@pytest.fixture
def fixture(tmp_path,monkeypatch):
    from app.services import production_source_configuration as configuration
    from app.services import codex_runtime_binding as binding
    from app.services import production_source_context as context
    from app.services import selected_source_registration as selected
    from app.services import selected_run_lifecycle as lifecycle
    from app.services import prospective_class_c_owner as registration
    from app.services import kiwoom_global_lane as lane

    operating=tmp_path/'operating'
    review=tmp_path/'review'
    for root in (operating,review):
        (root/'data').mkdir(parents=True)
        (root/'data/thesis_monitor.sqlite3').write_bytes(b'EMPTY_NOT_A_DATABASE')
    (operating/'.env').touch()
    lock=tmp_path/'synthetic-lane.lock'
    lock.touch()
    observed=dict(target_roots=[],capture_roots=[],approval_stubs=0,ledger_options=[])
    settings=SimpleNamespace(database_url='sqlite:///./data/thesis_monitor.sqlite3')
    source=SimpleNamespace(database_path=str(operating/'data/thesis_monitor.sqlite3'),
        seal_protocols=lambda *a:{})
    monkeypatch.setattr(job,'ROOT',review)
    monkeypatch.setattr('app.config.Settings',lambda **kw:settings)
    monkeypatch.setattr(configuration.ProductionSourceConfiguration,'model_validate_json',lambda *a:source)
    monkeypatch.setattr(binding,'binding_from_json',lambda v:SimpleNamespace(executable='SYNTHETIC_ONLY'))
    monkeypatch.setattr(binding,'parent_environment',lambda v:{})
    monkeypatch.setattr(binding,'validate_binding',lambda *a,**kw:None)
    monkeypatch.setenv('KIWOOM_GLOBAL_LANE_REQUIRED','1')
    monkeypatch.delenv('CODEX_HOME',raising=False)
    import os
    monkeypatch.setattr(lane,'configured_lane',lambda:SimpleNamespace(
        _open=lambda:os.open(lock,os.O_RDONLY),_state=lambda:None))
    monkeypatch.setattr(context,'inspect_native',lambda *a:{})
    monkeypatch.setattr(context,'credential_binding',lambda *a:{})
    def target(settings,*,runtime_directory):
        observed['target_roots'].append(runtime_directory)
        result=database_target(settings,runtime_directory=runtime_directory)
        observed['target']=result
        return result
    monkeypatch.setattr(selected,'database_target',target)
    def approve(decision):
        observed['approval_stubs']+=1
        return object()
    monkeypatch.setattr(registration,'record_backend_approval',approve)
    monkeypatch.setattr(registration,'revoke_approval',lambda v:None)
    def ledger(**kw):
        observed['ledger_options'].append(kw)
        return SimpleNamespace(state=lambda:{'state':'STOPPED_NO_SEND'},stop=lambda v:None)
    monkeypatch.setattr(lifecycle,'SelectedRunLedger',ledger)
    def capture(**kw):
        observed['capture_roots'].append(kw['runtime_directory'])
        assert kw['settings'].database_url=='sqlite:///./data/thesis_monitor.sqlite3'
        raise CaptureReached('STOP_BEFORE_ANY_REAL_OWNER_OR_DATABASE_CAPTURE')
    monkeypatch.setattr(selected,'capture_approved_markets',capture)
    def config(market='us'):
        wire=SimpleNamespace(read=lambda:b'{}')
        return SimpleNamespace(market=market,settings_env_file=str(operating/'.env'),source_configuration=wire,
            model_binding=wire,endpoint_rules=SimpleNamespace(read=lambda:json.dumps(job.LOCAL_CAPS[market]).encode()),
            code_commit='a'*40,model_dump=lambda **kw:dict(market=market,scope='SYNTHETIC_TEST_ONLY'))
    return SimpleNamespace(operating=operating,review=review,observed=observed,settings=settings,
        source=source,config=config,tmp=tmp_path)


def test_relative_db_and_capture_share_operating_env_root_without_url_rewrite(fixture):
    f=fixture
    for market in ('us','kr'):
        with pytest.raises(CaptureReached):
            asyncio.run(job._local_registered_cycle(f.config(market),f.tmp/market,'2026-11-18'))
    expected=f.operating/'data/thesis_monitor.sqlite3'
    assert f.observed['target_roots']==f.observed['capture_roots']==[f.operating,f.operating]
    assert f.observed['target']==(expected,expected.stat().st_dev,expected.stat().st_ino)
    assert f.settings.database_url=='sqlite:///./data/thesis_monitor.sqlite3'
    assert all((r/'data/thesis_monitor.sqlite3').read_bytes()==b'EMPTY_NOT_A_DATABASE' for r in (f.operating,f.review))
    assert [v['max_models'] for v in f.observed['ledger_options']]==[30,18]
    assert [v['timeout_retry_cap'] for v in f.observed['ledger_options']]==[1,0]


def test_different_pinned_database_or_env_folder_stops_before_owner(fixture):
    f=fixture
    f.source.database_path=str(f.review/'data/thesis_monitor.sqlite3')
    with pytest.raises(ValueError,match='local_schedule_active_database_mismatch'):
        asyncio.run(job._local_registered_cycle(f.config(),f.tmp/'mismatch','2026-11-18'))
    f.source.database_path=str(f.operating/'data/thesis_monitor.sqlite3')
    config=f.config()
    config.settings_env_file=str(f.review/'.env')
    with pytest.raises(ValueError,match='local_schedule_active_database_mismatch'):
        asyncio.run(job._local_registered_cycle(config,f.tmp/'wrong-root','2026-11-18'))
    assert f.observed['approval_stubs']==0 and not f.observed['capture_roots']


def test_original_symlink_and_sqlite_url_guards_remain(fixture):
    f=fixture
    target=f.operating/'data/thesis_monitor.sqlite3'
    target.unlink()
    target.symlink_to(f.review/'data/thesis_monitor.sqlite3')
    with pytest.raises(ValueError,match='selected_registration_symlink_denied'):
        asyncio.run(job._local_registered_cycle(f.config(),f.tmp/'symlink','2026-11-18'))
    for url in ('sqlite://','sqlite:///:memory:','sqlite:///file?mode=ro','postgresql://localhost/other'):
        f.settings.database_url=url
        with pytest.raises(ValueError,match='selected_exact_local_sqlite_target_required'):
            asyncio.run(job._local_registered_cycle(f.config(),f.tmp/'bad-url','2026-11-18'))
    assert f.observed['approval_stubs']==0 and not f.observed['capture_roots']


def test_only_runtime_root_assignment_and_two_arguments_change():
    repo=Path(__file__).resolve().parents[1]
    old=ast.parse(subprocess.check_output(['/usr/bin/git','-C',str(repo),'show',BASE+':app/jobs/unified_market_snapshot.py']))
    current=ast.parse((repo/'app/jobs/unified_market_snapshot.py').read_bytes())
    function=next(n for n in current.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='_local_registered_cycle')
    assignment=next(n for n in function.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='runtime_db_root' for t in n.targets))
    assert ast.dump(assignment.value)==ast.dump(ast.parse('Path(config.settings_env_file).parent',mode='eval').body)
    function.body.remove(assignment)
    calls=[n for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
        and n.func.id in {'database_target','capture_approved_markets'}]
    assert len(calls)==2
    for call in calls:
        keyword=next(k for k in call.keywords if k.arg=='runtime_directory')
        assert isinstance(keyword.value,ast.Name) and keyword.value.id=='runtime_db_root'
        keyword.value=ast.Name(id='ROOT',ctx=ast.Load())
    assert ast.dump(current)==ast.dump(old)
