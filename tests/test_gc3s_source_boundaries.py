"""Focused Cold shape checks; no credentials or external data."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import hashlib
import json
import pytest
from app.services import registered_source_batch as b


def cold_case():
    batch=b.Batch('GC3S_SYNTHETIC',('fictional-security',),('adjusted_daily',),
        (('kr','2026-11-03'),('us','2026-11-03')),
        (datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),2)
    rows=[dict(date='2026-11-02',close=10),dict(date='2026-11-03',close=11)]
    raw=json.dumps(rows).encode();plan=dict(generation_id='TEST_ONLY',parent_receipt_sha256='a'*64)
    receipt=dict(entry_id='fictional',security_id='fictional-security',target_session='2026-11-03',
        generation_id='TEST_ONLY',plan_sha256=b.digest(plan),parent_receipt_sha256='a'*64,
        consumer='SCOPED_SOURCE_ONLY',allowed_use='BOUND_SOURCE_ROWS_ONLY',normalized_sha256=b.digest(rows),
        rows=2,requested_rows=2)
    for key in ('technical_signal','completed_price_authority','financial_use','valuation_use','economic_use','D01_D02','native_use','full22_native','model_use'):
        receipt[key]=False
    receipt['receipt_sha256']=b.digest(receipt)
    data=dict(batch=batch.public(),contract='registered-source-batch-cold-v1',batch_id=batch.batch_id,
        batch_sha256=b.digest(batch.public()),plan=plan,receipts=[receipt],
        artifacts=[dict(entry_id='fictional',sha256=hashlib.sha256(raw).hexdigest())],
        expected_reads=[dict(entry_id='fictional',role='adjusted_daily',canonical_security_id='fictional-security',
            latest_completed_session='2026-11-03',market='kr',count=2)])
    return data,lambda _:(raw,rows)


def test_cold_positive_bytes_never_reissue_live_authority():
    data,reader=cold_case();result=b.validate_cold_roles(data,reader)
    assert result['status']=='BATCH_SEALED_BYTES_COLD_PASS_NOT_OWNER_REISSUANCE'
    assert result['new_live_authority'] is False


@pytest.mark.parametrize('key',['entry_id','receipt_sha256','model_use'])
def test_malformed_receipt_rejected_before_artifact_read(key):
    data,_=cold_case();del data['receipts'][0][key]
    with pytest.raises(ValueError,match='cold_required_fields'):
        b.validate_cold_roles(data,lambda _:pytest.fail('malformed receipt read data'))


def test_malformed_role_and_model_promotion_are_rejected():
    data,reader=cold_case();bad=deepcopy(data);del bad['expected_reads'][0]['count']
    with pytest.raises(ValueError,match='cold_required_fields'):b.validate_cold_roles(bad,reader)
    data['receipts'][0]['model_use']=True
    core=dict(data['receipts'][0]);core.pop('receipt_sha256')
    data['receipts'][0]['receipt_sha256']=b.digest(core)
    with pytest.raises(ValueError,match='cold_scope'):b.validate_cold_roles(data,reader)


def test_restore_uses_original_onboarding_and_never_imports_old_eligibility(tmp_path,monkeypatch):
    from sqlmodel import SQLModel,Session,create_engine,select
    from app.config import get_settings
    from app.models.watchlist import WatchlistItem
    from app.models.security import SecurityMaster
    from app.services.registration_seed_restore import restore_operator_registration
    monkeypatch.setenv('DATA_DIR',str(tmp_path));get_settings.cache_clear()
    seed=dict(watchlistitem=[dict(id=11,ticker='FICTIONAL',company_name='Fictional',exchange='NASDAQ',
        active=True,production_eligible=True,activated_at='2020-01-01T00:00:00+00:00')],
        securitymaster=[dict(id=12,ticker='FICTIONAL',company_name='Fictional',exchange='NASDAQ',country='US',
            canonical_company_id='fictional-issuer',canonical_security_id='fictional-security',
            issuer_type='domestic_us',updated_at='2020-01-01T00:00:00+00:00')],
        company=[dict(id=13,ticker='FICTIONAL',company_name='Fictional',exchange='NASDAQ',ir_url=None,
            filings_url=None,created_at='2020-01-01T00:00:00+00:00')],
        investmentthesis=[dict(id=14,ticker='FICTIONAL',version=1,core_thesis='Synthetic user definition',status='active')])
    engine=create_engine('sqlite:///'+str(tmp_path/'restore.sqlite3'));SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        result=restore_operator_registration(session,seed,deepcopy(seed),expected=('FICTIONAL',))
        watch=session.exec(select(WatchlistItem)).one();security=session.exec(select(SecurityMaster)).one()
        assert result['counts']=={'REGISTERED_PENDING_ONBOARDING':1}
        assert watch.id==11 and not watch.active and not watch.production_eligible
        assert watch.activated_at is None and watch.first_eligible_session is None
        assert security.updated_at.year==2020 and not result['current_source_authority']
    engine.dispose();get_settings.cache_clear()


def test_conflicting_seed_identity_isolated_before_restore(tmp_path):
    from sqlmodel import SQLModel,Session,create_engine
    from app.services.registration_seed_restore import restore_operator_registration
    seed={t:[] for t in ('watchlistitem','securitymaster','company','investmentthesis')}
    seed['watchlistitem']=[dict(ticker='FICTIONAL')]
    seed['company']=[dict(ticker='FICTIONAL')]
    seed['securitymaster']=[dict(ticker='FICTIONAL',canonical_security_id='one')]
    other=deepcopy(seed);other['securitymaster'][0]['canonical_security_id']='different'
    engine=create_engine('sqlite:///'+str(tmp_path/'conflict.sqlite3'));SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        result=restore_operator_registration(session,seed,other,expected=('FICTIONAL',))
        assert result['records'][0]['reason']=='SEED_IDENTITY_CONFLICT'
    engine.dispose()
