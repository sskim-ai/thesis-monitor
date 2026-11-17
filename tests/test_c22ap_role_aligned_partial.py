"""Changed C22AP boundaries only; mock wire is never live-source proof."""
import asyncio
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from app.providers.kiwoom_rest_client import KiwoomRestClient
from app.services.kiwoom_kr_market_context_service import (
    KiwoomKrMarketContextService, kiwoom_market_reads, validate_market_reads)
from app.services.canonical_source_replay import aggregate
from app.services.unified_aggregate_owners import kiwoom_aggregate_owner
from app.services.unified_aggregate_receipt import verify_aggregate
from app.services.unified_kiwoom_observer import KiwoomReceiptObserver
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_source_composition import SourceRole,A
from tests.test_kiwoom_rest_market_context import _handler,SESSION_DATE,OBSERVED_AT


def captured(tmp_path, detail):
    full=kiwoom_market_reads(session_date=SESSION_DATE,max_pages=5,max_requests_per_page=1)
    reads=full if detail else tuple(r for r in full if r.api_id!='ka10066')
    policy=UnifiedSourcePolicy(frozenset({'kiwoom_rest'}))
    root=tmp_path/('full' if detail else 'selected')
    observer=KiwoomReceiptObserver(root=root,run_id='C22AP_SYNTHETIC',attempt_id='A1',
        session_date=SESSION_DATE,reads=reads,policy=policy,completed_session_only=True)
    calls=[]
    client=KiwoomRestClient(app_key='synthetic',secret_key='synthetic',source_observer=observer,
        transport=_handler(calls),max_retries=0,request_interval_seconds=0)
    result=asyncio.run(KiwoomKrMarketContextService(client,max_pages=5,completed_session_only=True).collect(
        session_date=SESSION_DATE,observed_at=OBSERVED_AT))
    norm=json.loads((root/'normalization.json').read_bytes())
    role=SourceRole(key='kr_local_indices_sectors_breadth',owner='kiwoom_pages',market='kr',symbol='*',
        provider='kiwoom_rest',basis='query_time',session=str(SESSION_DATE),acquisition_class=A,mandatory=True)
    receipt=aggregate(root,role,norm['roles'][role.key]['value'])
    cutoff=datetime.now(timezone.utc)
    graph=verify_aggregate(root,receipt,policy=policy,cutoff=cutoff,completion_observed_at=OBSERVED_AT)
    owner=kiwoom_aggregate_owner(role=role,observed_at=OBSERVED_AT,max_pages=5,
        max_requests_per_page=1,policy=policy,consumer_complete=True,selected_reads=reads)
    return result,norm,owner,graph,cutoff,calls,reads


def test_selected_eight_and_legacy_ten_reach_real_parent_and_consumer(tmp_path):
    for detail in (False,True):
        result,norm,owner,graph,cutoff,calls,reads=captured(tmp_path,detail)
        assert norm['mandatory_complete']
        assert norm['field_claim_limits']['aggregate_flows']=='AVAILABLE'
        assert norm['field_claim_limits']['concentration']==('AVAILABLE' if detail else 'UNAVAILABLE')
        assert len(calls)==(12 if detail else 8)
        assert len(result.cross_section.market_flows)==6
        assert bool(result.audit.concentration)==detail
        projection=owner.project_aggregate_and_validate(graph,cutoff)
        assert projection.value==norm['roles']['kr_local_indices_sectors_breadth']['value']
        assert len(graph.child_receipts)==len(calls)
        assert [r.key for r in reads]==[r['key'] for r in json.loads(graph.plan)['reads']]


def test_wrong_role_set_body_market_session_and_cursor_never_pass_by_count(tmp_path):
    result,norm,owner,graph,cutoff,calls,reads=captured(tmp_path,False)
    for wrong in (reads[:-1],(*reads[:-1],reads[0]),tuple(reversed(reads)),
            (reads[0].model_copy(update={'body':dict(mrkt_tp='1',inds_cd='001')}),*reads[1:])):
        with pytest.raises(ValueError,match='role_set_mismatch'):
            validate_market_reads(wrong,session_date=SESSION_DATE,max_pages=5,max_requests_per_page=1)
    for mutate in ('order','cursor','body','session','missing'):
        receipts=deepcopy(graph.child_receipts)
        plan=json.loads(graph.plan)
        if mutate=='order':receipts=tuple(reversed(receipts))
        elif mutate=='cursor':receipts[0]['request']['cursor_sha256']='f'*64
        elif mutate=='body':receipts[0]['request']['body']['inds_cd']='101'
        elif mutate=='session':plan['session']='2026-08-24'
        else:receipts=receipts[:-1]
        with pytest.raises(ValueError):
            owner.project_aggregate_and_validate(replace(graph,child_receipts=receipts,plan=json.dumps(plan).encode()),cutoff)


def test_raw_body_tampering_is_rejected_before_consumer(tmp_path):
    result,norm,owner,graph,cutoff,calls,reads=captured(tmp_path,False)
    # Verification, not candidate normalization equality, owns raw integrity.
    source=tmp_path/'selected/read-0001.body'
    source.write_bytes(source.read_bytes()+b' ')
    with pytest.raises(ValueError):
        verify_aggregate(tmp_path/'selected',graph.receipt,policy=UnifiedSourcePolicy(frozenset({'kiwoom_rest'})),
            cutoff=cutoff,completion_observed_at=OBSERVED_AT)


def test_missing_sibling_does_not_revoke_verified_comparison_or_grant_missing_claim():
    from app.services.sec_financial_source_completeness import field_completeness
    selection=dict(fields=dict(revenue=dict(status='PASS'),
        operating_income=dict(status='BLOCKED',denial_reasons=['NO_EXACT_COMPARABLE_PRIOR'])))
    documents=[dict(occurrences=[],valid_occurrence_ids=[],inline_owner=dict(denials=[]))]
    complete=dict(bounded_plan_complete=False,reasons=['PURPOSE_UNRESOLVED'],receipt_sha256='a'*64,
        current_generation_eligible=True)
    value=field_completeness(selection,documents,complete)
    assert value['partial_field_consumption_allowed'] is True
    assert value['field_claim_limits']['revenue']['growth_claim'] is True
    assert value['field_claim_limits']['operating_income']['growth_claim'] is False
    assert value['field_claim_limits']['operating_income']['zero_imputation'] is False
    assert value['field_claim_limits']['revenue']['valuation_or_per_share_grant'] is False
    complete['current_generation_eligible']=False
    assert not field_completeness(selection,documents,complete)['partial_field_consumption_allowed']


def test_manual_job_is_due_plus_300_and_crash_intent_never_refills(tmp_path):
    from app.services.vnext_one_shot_schedule import manual_one_shot_plan,consume_manual_intent
    at=datetime(2026,11,12,10,0,27,tzinfo=timezone.utc)
    plan=manual_one_shot_plan(label='local.thesis-monitor.one-shot.c22ap-test',
        program=['/usr/bin/python3','/private/tmp/test.py'],working_directory='/private/tmp',
        armed_at=at,expires_at=at+timedelta(hours=1),binding=dict(result_root=str(tmp_path)))
    assert datetime.fromisoformat(plan['due_at'])==at+timedelta(seconds=300)
    assert plan['markets']==['kr','us'] and not plan['repeat']
    assert not plan['plist']['RunAtLoad'] and not plan['plist']['KeepAlive']
    intent=tmp_path/'CONSUMED.json'
    with pytest.raises(ValueError):consume_manual_intent(intent,plan=plan,actual_started_at=at)
    consume_manual_intent(intent,plan=plan,actual_started_at=at+timedelta(seconds=300))
    original=intent.read_bytes()
    with pytest.raises(FileExistsError):
        consume_manual_intent(intent,plan=plan,actual_started_at=at+timedelta(seconds=301))
    assert intent.read_bytes()==original


def test_manual_current_activation_keeps_regular_future_date_and_original_owner(tmp_path,monkeypatch):
    import sqlite3
    from types import SimpleNamespace
    from app.services import minimal_class_c_export as export
    from app.services import selected_source_registration as registration
    from app.services import prospective_class_c_owner as prospective
    from app.services.onboarding_readiness_service import canonical_registration_eligibility
    from app.services.unified_snapshot_contract import digest
    from tests.test_c22an_registration_and_cohorts import synthetic_campaign
    from tests.test_minimal_class_c_export import POLICY
    c=synthetic_campaign(tmp_path,monkeypatch)
    at=datetime(2026,11,12,9,0,tzinfo=timezone.utc)
    c.now[0]=at
    activation=at-timedelta(hours=1)
    with sqlite3.connect(c.permission.database) as db:
        db.execute('UPDATE watchlistitem SET activated_at=? WHERE ticker=?',(activation.isoformat(),'CORZ'))
    event=dict(trigger_kind='MANUAL_ONE_SHOT',armed_at=(at-timedelta(minutes=10)).isoformat(),
        due_at=(at-timedelta(minutes=5)).isoformat(),actual_started_at=(at-timedelta(minutes=5)).isoformat(),
        expires_at=(at+timedelta(hours=1)).isoformat(),OS_registered_process_verified=True)
    saved={}
    def proofs(capture):
        raw,_=export.captured_private_snapshot(capture)
        rows=json.loads(raw)
        models={t:export.MODELS[t].model_validate(next(r for r in rs if r['ticker']=='CORZ'))
            for t,rs in rows.items()}
        hashes={t:digest(r.model_dump(mode='json')) for t,r in models.items()}
        proof=dict(assignment_kind='REGULAR_BATCH',writer='resume_onboarding_subject',
            explicit_first_session=None,record_hashes=hashes,
            writer_result=dict(active=True,production_eligible=True,first_eligible_session='2026-11-13'))
        saved.update(models=models,proof=proof)
        return {'CORZ':proof}
    capture,owners,receipt=registration.capture_approved_markets(settings=SimpleNamespace(
        database_url='sqlite:///'+str(c.permission.database)),runtime_directory=tmp_path,
        approval=c.approval,generations={'us':'SYNTHETIC_us'},policy=POLICY,ledger=c.ledger,
        enabled=True,subject_limits={'us':1},priority_subjects={'us':('CORZ',)},
        execution=event,regular_assignments=proofs)
    document,owner_receipt=prospective._state(owners['us'])
    assert owner_receipt['bindings']['CORZ']['original_first_eligible_session']=='2026-11-13'
    assert document['universe']['eligible_subjects']==['CORZ']
    assert prospective.replay_captured_local_seed(owners['us'],policy=POLICY)==document
    m=saved['models']
    args=dict(ticker='CORZ',item=m['watchlistitem'],security=m['securitymaster'],
        thesis=m['investmentthesis'],company=m['company'],cutoff=at)
    assert not canonical_registration_eligibility(**args)['canonical_eligible']
    assert canonical_registration_eligibility(**args,execution=event,
        regular_assignment=saved['proof'])['canonical_eligible']
    explicit={**saved['proof'],'assignment_kind':'EXPLICIT_EFFECTIVE_DATE'}
    assert not canonical_registration_eligibility(**args,execution=event,
        regular_assignment=explicit)['canonical_eligible']
    m['watchlistitem'].active=False
    assert not canonical_registration_eligibility(**args,execution=event,
        regular_assignment=saved['proof'])['canonical_eligible']


def test_one_shot_clock_is_not_a_fake_regular_slot():
    from types import SimpleNamespace
    from datetime import date
    from app.services.unified_cycle_owner import _clock
    at=datetime(2026,11,12,9,0,tzinfo=timezone.utc)
    event=dict(trigger_kind='MANUAL_ONE_SHOT',armed_at=(at-timedelta(minutes=10)).isoformat(),
        due_at=(at-timedelta(minutes=5)).isoformat(),actual_started_at=(at-timedelta(minutes=5)).isoformat(),
        expires_at=(at+timedelta(hours=1)).isoformat(),OS_registered_process_verified=True)
    freeze=SimpleNamespace(market='us',scheduled_at=at-timedelta(minutes=5),cutoff=at,
        trigger_kind='MANUAL_ONE_SHOT',execution_event=event)
    assert _clock(freeze,date(2026,11,11))['target']=='2026-11-11'
    freeze.trigger_kind='REGULAR_SCHEDULED'
    with pytest.raises(ValueError,match='slot_not_owned'):_clock(freeze,date(2026,11,11))


def test_explicit_revalidation_preserves_dated_rows_spend_and_single_read(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from app.services import selected_source_registration as registration
    from app.services import prospective_class_c_owner as prospective
    from app.services.minimal_class_c_export import captured_source_cutoff
    from tests.test_c22an_registration_and_cohorts import synthetic_campaign
    from tests.test_minimal_class_c_export import POLICY
    c=synthetic_campaign(tmp_path,monkeypatch)
    c.now[0]=datetime(2026,11,12,8,0,tzinfo=timezone.utc)
    kwargs=dict(settings=SimpleNamespace(database_url='sqlite:///'+str(c.permission.database)),
        runtime_directory=tmp_path,approval=c.approval,generations={'kr':'SYNTHETIC_kr'},
        policy=POLICY,ledger=c.ledger,enabled=True)
    _,owners,prior=registration.capture_approved_markets(**kwargs)
    c.ledger.market_failed('kr','SYNTHETIC_OLD_LOCAL_FAILURE')
    prefix=c.ledger.path.read_bytes()
    del owners
    c.now[0]+=timedelta(hours=2)
    capture,owners,current=registration.capture_approved_markets(**kwargs,
        reference_captures={'kr':prior},revalidation_work_order_sha256='a'*64)
    _,receipt=prospective._state(owners['kr'])
    assert current['cutoff']!=prior['cutoff']
    assert receipt['cutoff']==prior['cutoff']
    assert receipt['actual_current_capture_at']==current['cutoff']
    assert captured_source_cutoff(capture,reference_capture=prior)==prior['cutoff']
    assert prospective.replay_captured_local_seed(owners['kr'],policy=POLICY)
    state=c.ledger.state()
    assert state['db_connection_attempts']==2 and state['db_select_actual']==10
    assert state['http_total']==state['model_total']==0
    assert 'kr' in state['failed_markets']
    assert c.ledger.path.read_bytes().startswith(prefix)
    with pytest.raises(ValueError):
        registration.capture_approved_markets(**kwargs,revalidation_work_order_sha256='a'*64)
    assert c.ledger.state()['db_connection_attempts']==2
    wrong={**prior,'original_rows_sha256':'f'*64}
    with pytest.raises(ValueError,match='exact_original_rows'):
        captured_source_cutoff(capture,reference_capture=wrong)


def test_local_output_rejection_keeps_spend_and_other_market_but_not_transport_failure(tmp_path,monkeypatch):
    from tests.test_c22an_registration_and_cohorts import synthetic_campaign
    c=synthetic_campaign(tmp_path,monkeypatch)
    state=c.ledger.state()
    key='MODEL:SYNTHETIC:market'
    state.update(pending=key,state='MODEL_BUDGETED',model_total=1,monitoring_model_total=1)
    state['used'][key]=dict(kind='MODEL',market='kr')
    c.ledger._apply(state,'MODEL_OUTPUT_REJECTED',dict(key=key,reason='CANONICAL_OUTPUT_VALIDATION_REJECTED'))
    assert state['pending'] is None and key in state['used'] and key in state['completed']
    assert state['model_total']==1 and state['state']=='APPROVED_FROZEN_RUN'
    assert set(state['failed_markets'])=={'kr'}
    wrong=deepcopy(state);wrong['pending']=key;wrong['runtime']={'first_external_failure':{'status':401}}
    with pytest.raises(ValueError,match='not_admissible'):
        c.ledger._apply(wrong,'MODEL_OUTPUT_REJECTED',dict(key=key,reason='CANONICAL_OUTPUT_VALIDATION_REJECTED'))


def test_unknown_schema_validator_and_renderer_do_not_require_fake_numeric_facts():
    from scripts import r2b_r2_contract as contract
    recovery={'missing:comparison':dict(kind='COMPARABLE_FINANCIAL_OBSERVATION')}
    cap={k:[] for k in contract.DIRECTION_BUCKETS}
    output=dict(decision_mode='UNKNOWN_LIMIT',overall_direction='OBSERVE',new_buyer='OBSERVE',holder='OBSERVE',
        directional_buy_score=None,directional_sell_score=None,confidence=None,
        limitation_reason='ZERO_AUTHORIZED_DIRECTIONAL_EVIDENCE',unknowns=list(recovery),required_next_evidence=list(recovery))
    assert contract.validate_unknown(output,mode='UNKNOWN_LIMIT',recovery=recovery,capability=cap)['status']=='PASS'
    assert contract.unknown_schema(recovery)
    assert contract.render_unknown('SYNTHETIC',output,recovery=recovery,capability=cap)
    with pytest.raises(Exception):
        contract.validate_unknown(dict(output,overall_direction='BUY'),mode='UNKNOWN_LIMIT',recovery=recovery,capability=cap)


def test_cli_nested_error_code_classification_does_not_retry_or_parse_model_prose():
    from app.services.official_codex_production_executor import _availability_failure
    error=dict(type='error',status=400,error=dict(type='invalid_request_error',code='model_not_found'))
    rows=[error,dict(type='error',message=json.dumps(error)),
        dict(type='turn.failed',error=dict(message=json.dumps(error)))]
    for row in rows:
        assert _availability_failure(json.dumps(row).encode())=='MODEL_ENTITLEMENT_OR_QUOTA_UNAVAILABLE'
    for row in (dict(type='item.completed',item=dict(type='agent_message',text=json.dumps(error))),
            dict(type='error',message='model_not_found'),dict(type='error',message='{broken'),
            dict(type='error',error=dict(code='authentication_error'))):
        assert _availability_failure(json.dumps(row).encode())=='PROCESS_NONZERO'
