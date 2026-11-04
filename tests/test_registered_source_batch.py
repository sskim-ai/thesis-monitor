"""P3-only focused contract coverage. No real DB, Provider or model execution."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import hashlib
import json
from pathlib import Path

import pytest

from app.services import registered_source_batch as b
from tests.test_manual_scoped_source_runtime import case, p2g_case, POLICY, CONFIG


def batch(**changes):
    value=b.Batch('P3_SYNTHETIC_BATCH',('fictional-security',),('adjusted_weekly',),
        (('kr','2026-11-03'),('us','2026-11-03')),
        (datetime.now(timezone.utc)+timedelta(minutes=30)).isoformat(),16).public()
    value.update(changes)
    return b.Batch.parse(value)


def test_exact_versioned_batch():
    value=batch()
    assert b.Batch.parse(value.public())==value
    value.validate()


def test_empty_and_unknown_arguments_fail_closed():
    with pytest.raises(ValueError):batch(roles=[],security_ids=[])
    value=batch().public();value['approved']=True
    with pytest.raises(ValueError):b.Batch.parse(value)


def test_purpose_and_contract_are_not_labels_for_authority():
    with pytest.raises(ValueError):batch(purpose='PRODUCTION')
    with pytest.raises(ValueError):batch(contract='registered-source-batch-v0')


def test_duplicate_and_unbounded_security_selection():
    with pytest.raises(ValueError):batch(security_ids=['same','same'])
    with pytest.raises(ValueError):batch(security_ids=[str(n) for n in range(23)])


def test_roles_and_prices_are_explicit():
    with pytest.raises(ValueError):batch(roles=['unadjusted_daily'])
    with pytest.raises(ValueError):batch(independent_us_closes=True)


def test_current_expiry_and_completed_session_are_separate():
    value=batch();now=datetime.now(timezone.utc)
    value.require_current(now,dict(value.sessions))
    with pytest.raises(ValueError):value.require_current(now+timedelta(hours=2),dict(value.sessions))
    with pytest.raises(ValueError):value.require_current(now,dict(kr='2026-11-04',us='2026-11-03'))


def test_original_retry_and_command_limits_not_extended():
    with pytest.raises(ValueError):batch(maximum_http=65)
    with pytest.raises(ValueError):batch(maximum_http=True)
    with pytest.raises(ValueError):batch(timeout_seconds=601)
    with pytest.raises(ValueError):batch(security_ids=['1','2','3'],roles=list(b.ROLES))


def test_batch_space_is_derived_not_full_guard_substitution(tmp_path):
    small=b.admission_bytes(batch());large=b.admission_bytes(batch(maximum_http=64))
    assert large['expected_incremental_peak_bytes']>small['expected_incremental_peak_bytes']
    assert small['reserve_bytes']==4*1024**3 and small['required_bytes']>=8*1024**3
    assert b.require_space(batch(),[tmp_path],retained_limit=0)[0]['scope']=='BATCH_ONLY_NOT_FULL_US_GUARD_REDUCTION'


def test_budget_checkpoint_and_concurrency_do_not_reissue():
    value=batch();budget=b.Budget(20);budget.start(value)
    with pytest.raises(ValueError):budget.start(value)
    with pytest.raises(ValueError):budget.finish(1,{'batch_id':'wrong'})
    budget.finish(6,{'batch_id':value.batch_id});assert budget.spent==6
    with pytest.raises(ValueError):budget.start(value)
    with pytest.raises(ValueError):budget.start(batch(batch_id='OTHER_SYNTHETIC_BATCH'))


def test_same_bytes_are_reuse_candidates_not_live_owner():
    old=dict(security_id='fictional',session='2026-11-03',provider='kiwoom',role='adjusted_daily',
        adjusted=True,raw_sha256='a'*64,receipt_sha256='b'*64,generation_id='old')
    result=b.reuse_candidate(old,deepcopy(old));assert not result['refetch'] and not result['source_owner_issued']
    changed=dict(old,session='2026-11-04')
    with pytest.raises(ValueError):b.reuse_candidate(old,changed)
    with pytest.raises(ValueError):b.reuse_candidate(old,old,live_reuse_owner={'approved':True})


def test_market_components_are_not_a_parent():
    assert b.market_status('CAPTURED')['parent']=='NOT_ISSUED'
    with pytest.raises(ValueError):b.market_status('CAPTURED',{'PASS':True})


def test_output_escape_and_byte_cap(tmp_path):
    (tmp_path/'blob').write_bytes(b'123')
    assert b.checked_tree(tmp_path,3)==3
    with pytest.raises(ValueError):b.checked_tree(tmp_path,2)
    (tmp_path/'link').symlink_to(tmp_path/'blob')
    with pytest.raises(ValueError):b.checked_tree(tmp_path,100)


def original_compile(case,roles,*,components=(),price=False):
    ids=tuple(min(r.canonical_security_id for r in case['stock'].reads if r.market==market) for market in ('kr','us'))
    if price:ids=(ids[1],)
    if components and not roles:ids=()
    value=batch(security_ids=list(ids),roles=list(roles),sessions=case['frozen']['sessions'],
        maximum_http=64,component_markets=list(components),independent_us_closes=price)
    return value,b.compile_batch(value,bridge=case['handle'],frozen=case['frozen'],stock=case['stock'],
        policy=POLICY,provider_sha=CONFIG)


def test_original_parent_accepts_all_four_roles_without_canary_change(case):
    from app.services.current_scoped_source_owner import resolve_parent,revoke_parent
    _,(parent,wire,stock)=original_compile(case,b.ROLES)
    try:
        assert len(wire['stock_reads'])==8
        assert {r.role for r in wire['stock_reads']}==set(b.ROLES)
        receipt=resolve_parent(parent,plan=wire['request_plan'])
        assert receipt['full22_native'] is False and receipt['financial_use'] is False
    finally:revoke_parent(parent)


def test_original_market_and_price_plans_have_distinct_scopes(case):
    from app.services.current_scoped_source_owner import resolve_parent,revoke_parent
    value,(parent,wire,_)=original_compile(case,(),components=('us',))
    try:
        assert len(wire['request_plan'].descriptors)==48 and not wire['stock_reads']
        assert resolve_parent(parent)['current_source_evidence']=='NOT_ISSUED'
    finally:revoke_parent(parent)
    # New generation/Owners are required after revocation; do not resurrect the
    # original market parent by reusing the same original registration anchor.
    price=batch(security_ids=['fictional-us'],roles=[],independent_us_closes=True)
    assert price.independent_us_closes and not price.component_markets


def cold_input():
    value=batch();rows=[dict(date='2026-10-30',close=1),dict(date='2026-11-03',close=2)]
    raw=json.dumps(rows).encode();entry='us:FICT:adjusted_weekly'
    plan=dict(generation_id='synthetic',parent_receipt_sha256='a'*64)
    receipt=dict(entry_id=entry,security_id='fictional-security',target_session='2026-11-03',
        generation_id='synthetic',plan_sha256=b.digest(plan),parent_receipt_sha256='a'*64,
        consumer='SCOPED_SOURCE_ONLY',allowed_use='BOUND_SOURCE_ROWS_ONLY',normalized_sha256=b.digest(rows),rows=2,requested_rows=2)
    for key in ('technical_signal','completed_price_authority','financial_use','valuation_use','economic_use',
                'D01_D02','native_use','full22_native','model_use'):receipt[key]=False
    receipt['receipt_sha256']=b.digest(receipt)
    data=dict(contract='registered-source-batch-cold-v1',batch_id=value.batch_id,batch=value.public(),
        batch_sha256=b.digest(value.public()),plan=plan,receipts=[receipt],
        artifacts=[dict(entry_id=entry,path='rows.json',sha256=hashlib.sha256(raw).hexdigest())],
        expected_reads=[dict(entry_id=entry,role='adjusted_weekly',canonical_security_id='fictional-security',
            latest_completed_session='2026-11-03',market='us',count=2)])
    return data,lambda artifact:(raw,rows)


def test_separate_cold_contract_is_readback_not_new_authority():
    data,reader=cold_input();result=b.validate_cold_roles(data,reader)
    assert result['new_live_authority'] is False
    data['batch_id']='DIFFERENT_BATCH'
    with pytest.raises(ValueError):b.validate_cold_roles(data,reader)


def test_cold_rejects_wrong_rows_generation_and_permissions():
    for mutation in ('generation_id','model_use','row_hash'):
        data,reader=cold_input()
        if mutation=='row_hash':data['artifacts'][0]['sha256']='0'*64
        else:
            receipt=data['receipts'][0];receipt.pop('receipt_sha256')
            receipt[mutation]='wrong' if mutation=='generation_id' else True
            receipt['receipt_sha256']=b.digest(receipt)
        with pytest.raises(ValueError):b.validate_cold_roles(data,reader)
