"""Default-OFF P3 batch CLI; original v3 entry and manifest stay unchanged."""
import argparse
import asyncio
from datetime import datetime,timedelta,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
NEW=('app/services/registered_source_batch.py','scripts/official_source_batch.py','scripts/official_source_batch_cold.py')


def pin(path):
    raw=Path(path).read_bytes();return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def read(path,expected):
    path=Path(path)
    if not path.is_absolute() or any(p.is_symlink() for p in (path,*path.parents)) or path.stat().st_size>128*1024:
        raise ValueError('p3_cli_input_path')
    if pin(path)['sha256']!=expected:raise ValueError('p3_cli_input_hash')
    return json.loads(path.read_bytes())


async def cold(m,batch,result,wire,output,*,external_root):
    from app.services.registered_source_batch import digest,require
    from app.services.unified_run_artifacts import durable_json
    request=dict(contract='registered-source-batch-cold-v1',batch_id=batch.batch_id,batch=batch.public(),
        batch_sha256=digest(batch.public()),capture=result['capture'],plan=result['plan'],
        receipts=result['receipts'],artifacts=result['row_artifacts'],physical_receipts=result['physical_receipts'],
        expected_reads=[r.model_dump(mode='json') for r in wire['stock_reads']],source_pins=m['source_pins'])
    if any(r.get('contract')=='current-scoped-role-source-receipt-v2-wm' for r in result['receipts']):
        request['external_root']=external_root
        request['external_pins']=m['original_external_code']
    path=output/'cold-input.json';durable_json(path,request,exclusive=True)
    raw=path.read_bytes()
    process=await asyncio.create_subprocess_exec(m['interpreter'],'-I','-B',
        str(ROOT/'scripts/official_source_batch_cold.py'),str(path),hashlib.sha256(raw).hexdigest(),
        stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,
        env={'PATH':'/usr/bin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'},cwd=str(output))
    async def bounded(stream,maximum):
        body=bytearray()
        while chunk:=await stream.read(4096):
            body.extend(chunk);require(len(body)<=maximum,'cold_output_limit')
        return bytes(body)
    try:
        stdout,stderr,_=await asyncio.wait_for(asyncio.gather(bounded(process.stdout,128*1024),
            bounded(process.stderr,4096),process.wait()),timeout=60)
    except BaseException:
        if process.returncode is None:process.kill()
        await process.communicate();raise
    require(process.returncode==0 and not stderr,'cold_process_failed')
    value=json.loads(stdout)
    require(value['pid']!=__import__('os').getpid() and value['input_sha256']==hashlib.sha256(raw).hexdigest()
        and value['receipt_set_sha256']==digest(request['physical_receipts'])
        and value['new_live_authority'] is False,'cold_identity')
    durable_json(output/'cold-receipt.json',value,exclusive=True)
    return value


async def run(m,cli,plan,plan_sha,batches):
    from app.services.registered_source_batch import (Budget,compile_batch,execute_chart_batch,
        require,require_space,digest,checked_tree)
    from app.services import source_parent_canary_v3 as v3
    from app.services import official_registered_source_runtime as registered
    from app.services import prospective_class_c_owner as prospective
    from app.services import current_class_c_source_bridge as registration
    from app.services.minimal_class_c_export import ExportPermission,capture_authorized_class_c,captured_private_snapshot
    from app.services.unified_run_artifacts import durable_json
    require(sys.stdin.isatty() and sys.stdout.isatty(),'owner_terminal_required')
    output=Path(plan['output_root'])
    require(not output.exists() and output.parent.is_dir(),'fresh_run_output')
    for batch in batches:require_space(batch,[output.parent],retained_limit=plan['retained_byte_limit'])
    session,host=v3.admit_parent(m,cli)
    approval=boundary=None
    report=dict(status='P3_BATCH_NOT_RUN',HTTP=0,DB_sessions=0,SELECT=0,batches=[],host=host,models=0)
    try:
        phrase=f"APPROVE P3A {plan['run_id']} {plan_sha} DB1_SELECT5_KIWOOM{plan['maximum_http']} NO_RETRY_NO_CONCURRENT_USE"
        print(phrase,flush=True);require(input().strip()==phrase,'owner_confirmation')
        now=datetime.now(timezone.utc);expiry=min(datetime.fromisoformat(b.expires_at) for b in batches)
        require(now<expiry<=now+timedelta(minutes=55),'run_expiry')
        approval=prospective.record_backend_approval(prospective.ApprovalDecision(event_id=plan['run_id'],
            user_message_sha256=digest(phrase.encode().hex()),approved=True,effective_at=now,
            expires_at=expiry,subjects=registered.registered_subjects()))
        boundary=v3.admit_readonly(plan['database'],approval,enabled=True)
        output.mkdir(mode=0o700)
        durable_json(output/'run-start.json',dict(plan_sha256=plan_sha,approval_phrase_sha256=hashlib.sha256(phrase.encode()).hexdigest(),
            entered_by='TTY_INPUT_WITH_EXACT_CURRENT_USER_GRANT',DB_boundary=v3.DB_POLICY,
            kernel_DB_write_isolation=False,original_v3_unchanged=True),exclusive=True)
        device,inode=v3.require_readonly(boundary,plan['database'],approval,consume=True)
        report['DB_sessions']=1
        capture=capture_authorized_class_c(ExportPermission(plan['run_id'],True,Path(plan['database']),device,inode,registered.registered_subjects()))
        _,receipt=captured_private_snapshot(capture)
        v3.require_readonly(boundary,plan['database'],approval)
        require(len(receipt['statement_templates'])==5 and receipt['total_changes']==0
            and receipt['sqlite_mode']=='ro' and receipt['query_only'] is True
            and not receipt['denied_queries']
            and receipt['snapshot']=='ONE_BEGIN_READ_TRANSACTION_ROLLBACK','registration_query_contract')
        report.update(SELECT=5,private_rows_exported=False)
        report['registration']=dict(tables=receipt['tables'],snapshot_sha256=receipt['original_rows_sha256'],
            cutoff=receipt['cutoff'],SELECT=5,sessions=1,total_changes=0)
        from app.config import Settings
        settings=Settings(_env_file=plan['settings_file'])
        public=dict(provider='kiwoom',base_url=settings.kiwoom_rest_base_url,
            interval=max(1.5,settings.kiwoom_rest_request_interval_seconds),retries=0)
        config_sha=digest(public);config_ids={name:digest(dict(provider=name,state='UNREQUESTED_NOT_CONFIGURED'))
            for name in ('sec_edgar','opendart','fred','eia','ecos','krx_night_futures','google_news_rss','naver_news')}
        config_ids['kiwoom']=config_sha
        policy=registered.original_identity_policy();budget=Budget(plan['maximum_http'])
        for batch in batches:
            from app.services.market_session import korea_market_session,us_market_session
            current=datetime.now(timezone.utc)
            batch.require_current(current,dict(kr=str(korea_market_session(current).latest_completed_regular_session_date),
                us=str(us_market_session(current).latest_completed_regular_session_date)))
            budget.start(batch);owners={};bridge=parent=None;batch_output=output/batch.batch_id
            try:
                if not batch.roles or batch.component_markets or batch.independent_us_closes:
                    result=dict(batch_id=batch.batch_id,status='BLOCKED_EXECUTOR_ROLE',physical_HTTP=0,
                        function='registered_source_batch.execute_chart_batch',
                        reason='Original Market/Price worker command and parent-use composition not qualified')
                else:
                    for market in ('kr','us'):
                        owners[market],_=prospective.issue_prospective_owner(approval=approval,capture=capture,
                            market=market,source_generation_id=plan['run_id']+'-registration',generation_id=batch.batch_id,policy=policy)
                    metadata=dict(run_id=batch.batch_id,acquisition_id=batch.batch_id+'-capture',
                        instruction_sha=plan['instruction_sha1'],implementation_sha=hashlib.sha1(json.dumps(m['source_pins'],sort_keys=True).encode()).hexdigest(),
                        owner_files={name:value['sha256'] for name,value in registered.original_external_pins(m,plan['external_code_contract']).items()},
                        owner_head=plan['external_head'],settings_sha256=config_sha,request_environment_sha256=config_sha)
                    counts={market:dict(adjusted_daily=1000,adjusted_weekly=700,adjusted_monthly=300,unadjusted_weekly_valuation=300) for market in ('kr','us')}
                    bridge,stock,frozen=registration.prepare_current_bridge(capture=capture,owners=owners,policy=policy,
                        stock_metadata=metadata,counts=counts,config_identities=config_ids,configured_kr_pages=20,
                        kr_post_acquisition_completeness_approved=True,enabled=True)
                    parent,wire,stock_wire=compile_batch(batch,bridge=bridge,frozen=frozen,stock=stock,policy=policy,provider_sha=config_sha)
                    require_space(batch,[output.parent],retained_limit=plan['retained_byte_limit'])
                    result=await execute_chart_batch(batch=batch,parent=parent,wire=wire,stock=stock_wire,
                        manifest=m,configuration=plan,settings=settings,session=session,output=batch_output)
                    parent=None
                    if result['receipts']:
                        result['cold']=await cold(m,batch,result,wire,batch_output,external_root=plan['external_root'])
                        result['status']='REAL_SOURCE_BATCH_AND_SEPARATE_COLD_PASS' if not result['gaps'] else 'REAL_SOURCE_BATCH_ROLE_PARTIAL'
                    checked_tree(output,plan['retained_byte_limit'])
                budget.finish(result['physical_HTTP'],result)
                report['batches'].append(result)
                report['HTTP']=budget.spent
                durable_json(output/f'checkpoint-{len(report["batches"]):03d}.json',dict(plan_sha256=plan_sha,
                    batch_id=batch.batch_id,session=dict(batch.sessions),result=result,
                    total_HTTP=budget.spent,completed_batch_ids=list(budget.done),checkpoint_is_not_live_authority=True),exclusive=True)
            except BaseException as exc:
                actual=0
                if (batch_output/'batch-runtime-end.json').exists():actual=json.loads((batch_output/'batch-runtime-end.json').read_bytes())['physical_HTTP']
                report['HTTP']=budget.spent+actual
                report['batches'].append(dict(batch_id=batch.batch_id,status='P3_BATCH_STOP_NO_RETRY',
                    error_type=type(exc).__name__,error_sha256=hashlib.sha256(str(exc).encode()).hexdigest(),physical_HTTP=actual))
                break
            finally:
                if parent is not None:
                    from app.services.current_scoped_source_owner import revoke_parent
                    revoke_parent(parent)
                if bridge is not None:registration.revoke_bridge(bridge)
                for handle in owners.values():
                    try:prospective.revoke_prospective_owner(handle)
                    except ValueError:pass
        report['status']='P3_GENERIC_BATCH_SOURCE_PROGRESS_NO_SEND' if any(b.get('cold') for b in report['batches']) else 'P3_BATCH_NO_CURRENT_SOURCE_ACCEPTED'
        return report
    finally:
        if approval is not None:prospective.revoke_approval(approval)
        if boundary is not None:v3.retire_readonly(boundary)
        session.close_admission()
        if output.exists():durable_json(output/'P3_EXECUTION_RESULT.json',report,exclusive=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release',required=True);parser.add_argument('--release-sha256',required=True)
    parser.add_argument('--plan',required=True);parser.add_argument('--plan-sha256',required=True)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    release=read(args.release,args.release_sha256);plan=read(args.plan,args.plan_sha256)
    candidate=release['contract']=='registered-source-batch-release-v2'
    if release['contract'] not in ('registered-source-batch-release-v1','registered-source-batch-release-v2') or release['default_enabled'] is not False:
        raise ValueError('p3_release_contract')
    expected_new=(*NEW,'app/services/wm_period_currentness.py','app/services/current_scoped_source_results.py',
        'scripts/official_source_canary_v3.py') if candidate else NEW
    if set(release['new_pins'])!=set(expected_new):raise ValueError('p3_release_code_scope')
    for name,expected in release['new_pins'].items():
        if pin(ROOT/name)!=expected:raise ValueError('p3_release_code_changed')
    old=ROOT/'ops/manual-source-parent-v3.json'
    if pin(old)['sha256']!=release['original_v3_manifest_sha256']:raise ValueError('p3_v3_identity')
    manifest=json.loads(old.read_bytes())
    launcher=ROOT/'scripts/official_source_canary_v3.py'
    expected_launcher=release['new_pins']['scripts/official_source_canary_v3.py'] if candidate else manifest['source_pins'][str(launcher.relative_to(ROOT))]
    if pin(launcher)!=expected_launcher:raise ValueError('p3_v3_entry_pin')
    scope={'__file__':str(launcher),'__name__':'p3_original_v3_loader'}
    exec(compile(launcher.read_bytes(),str(launcher),'exec',dont_inherit=True),scope)
    if candidate:
        item=release['manifest_candidate'];path=ROOT/item['path']
        proposed=read(path,item['sha256'])
        expected_pins={**manifest['source_pins'],**release['new_pins']}
        if proposed['source_pins']!=expected_pins:raise ValueError('p3_candidate_exact_pin_delta')
        m,cli=scope['validate_manifest'](path,item['sha256'],candidate=True)
    else:
        m,cli=scope['validate_manifest'](old,release['original_v3_manifest_sha256'])
    m=dict(m,source_pins={**m['source_pins'],**release['new_pins']})
    cli.bootstrap(m)
    from app.services.registered_source_batch import Batch,require,require_space
    require(plan['contract']=='registered-source-batch-run-v1' and plan['models']==0 and plan['delivery']=='NO_SEND','run_contract')
    batches=[Batch.parse(value) for value in plan['batches']]
    from app.services.market_session import korea_market_session,us_market_session
    current=datetime.now(timezone.utc)
    sessions=dict(kr=str(korea_market_session(current).latest_completed_regular_session_date),
        us=str(us_market_session(current).latest_completed_regular_session_date))
    for batch in batches:batch.require_current(current,sessions)
    for key in ('database','settings_file','external_root','output_root'):
        path=Path(plan[key])
        require(path.is_absolute() and not any(p.is_symlink() for p in (path,*path.parents)),'plain_plan_path')
    require(batches and len({b.batch_id for b in batches})==len(batches),'batch_list')
    require(sum(b.maximum_http for b in batches)<=plan['maximum_http'],'run_frozen_budget')
    require(plan['maximum_http']<=64 and plan['retained_byte_limit']<=512*1024**2,'reviewed_first_run_bound')
    resources=[require_space(batch,[Path(plan['output_root']).parent],retained_limit=plan['retained_byte_limit']) for batch in batches]
    if not args.execute:
        return dict(status='P3_EXECUTABLE_BATCH_REVIEW_NO_IO',batches=[b.public() for b in batches],
            resources=resources,DB=0,HTTP=0,models=0,current_grant=False)
    return asyncio.run(run(m,cli,plan,args.plan_sha256,batches))


if __name__=='__main__':
    try:print(json.dumps(main(),sort_keys=True))
    except BaseException as exc:
        print(json.dumps(dict(status='P3_REJECTED_NO_RETRY',error_type=type(exc).__name__,
            error_sha256=hashlib.sha256(str(exc).encode()).hexdigest())))
        raise SystemExit(2)
