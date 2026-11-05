import copy
import gzip
import hashlib
import json

import pytest

from app.services.dated_monitor_input import read_pinned, read_projection, preview
from app.services.unified_snapshot_contract import digest, encoded


@pytest.fixture
def source(tmp_path):
    read=dict(subject='EXAMPLE',role='adjusted_daily',timeframe='daily',adjusted=True,
              canonical_security_id='US:EXAMPLE',market='us',latest_completed_session='2026-11-04')
    identity=dict(read=read,generation='old-source',observed_at='2026-11-05T01:00:00+00:00',
                  raw_sha256=['a'*64],rows='b'*64,algorithm_sha='c'*64,adapter_sha='d'*64)
    p=dict(contract='historical-original-indicator-projection-v1',ticker='EXAMPLE',role='adjusted_daily',
           timeframe='daily',adjusted=True,basis='ADJUSTED_CHART',security_id='US:EXAMPLE',market='us',
           generation=identity['generation'],observed_at=identity['observed_at'],original_raw_sha=['a'*64],
           original_rows_sha='b'*64,algorithm_sha='c'*64,adapter_sha='d'*64,target_session='2026-11-04',
           current_eligibility=False,technical_signal=False,valuation_use=False,native_use=False,
           quote_finality='NOT_CLAIMED',last_valid_as_of='2026-11-04',valid_bars=1,invalid_rows=[],
           bars=[dict(date='2026-11-04',indicators={'MA5':None})],latest_availability={'MA5':{}})
    meta=dict(ticker='EXAMPLE',role='adjusted_daily',market='us',price_basis='ADJUSTED_CHART',
              source_generation='old-source',observed_at=identity['observed_at'],last_valid_as_of='2026-11-04',
              normalized_usable_rows='1',invalid_rows='0')
    path=tmp_path/'cache.gz'
    def write(projection=p,original=identity):
        raw=gzip.compress(encoded(dict(projection=projection,identity=original,projection_sha256=digest(projection))))
        path.write_bytes(raw)
        record=dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),projection_sha256=digest(projection),
                    ticker='EXAMPLE',role='adjusted_daily')
        m=meta|dict(cache_sha256=record['sha256'],calculation_sha=digest(projection))
        return record,m
    return p,identity,write


def test_original_null_preserved_without_calculation(source):
    p,i,write=source;r,m=write()
    assert read_projection(r,m)['bars'][0]['indicators']['MA5'] is None


@pytest.mark.parametrize('field,value',[
    ('ticker','OTHER'),('role','adjusted_monthly'),('timeframe','weekly'),('adjusted',False),
    ('basis','UNADJUSTED_CHART'),('security_id','US:OTHER'),('generation','new-source'),
    ('original_raw_sha',['e'*64]),('observed_at','2026-11-06T00:00:00+00:00'),
    ('current_eligibility',True),('technical_signal',True),('valuation_use',True),
    ('native_use',True),('quote_finality','FINAL'),('last_valid_as_of','2026-11-05')])
def test_rehashed_payload_cannot_change_contract(source,field,value):
    p,i,write=source;p=copy.deepcopy(p);p[field]=value;r,m=write(p)
    with pytest.raises(ValueError):read_projection(r,m)


def test_changed_cache_bytes(source):
    p,i,write=source;r,m=write();r['sha256']='0'*64
    with pytest.raises(ValueError,match='bytes_changed'):read_projection(r,m)


def test_symlink_is_not_cache_identity(source,tmp_path):
    p,i,write=source;r,m=write();link=tmp_path/'link';link.symlink_to(r['path'])
    with pytest.raises(ValueError,match='symlink'):read_pinned(link,r['sha256'])


def test_sealed_metadata_not_updated_to_fit_cache(source):
    p,i,write=source;r,m=write();m['invalid_rows']='99'
    with pytest.raises(ValueError,match='metadata'):read_projection(r,m)


def test_partial_universe_not_full22_preview():
    with pytest.raises(ValueError,match='22_by_4'):preview([],{'kr':{},'us':{}})
