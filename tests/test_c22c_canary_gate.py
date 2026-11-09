import hashlib,json,shutil
from pathlib import Path
import pytest
import httpx
from scripts import native_dwm_batch as batch


def test_first_daily_gate_reuses_real_prior_source_but_never_claims_live(tmp_path,monkeypatch):
    original=Path('/private/tmp/c21z-native22-20261109/kr-005930/daily')
    for name in ['response.body','NO_SEND.json']:shutil.copyfile(original/name,tmp_path/name)
    receipt=json.loads((original/'receipt.json').read_text())
    receipt.update(physical_cumulative_count=4,service_identity=dict(module_sha256='a'*64,pid=12345,maintenance='0',loaded_definitions_sha256='b'*64))
    monkeypatch.setattr(batch,'require_recovered_lane',lambda:None)
    def verify(r=receipt):
        return batch.verify_first_daily(tmp_path,r,symbol='005930',market='kr',physical_bound=16,expected_service_sha='a'*64,expected_service_pid=12345)
    assert verify()['native38']==38
    with pytest.raises(ValueError,match='physical_bound'):verify(dict(receipt,physical_cumulative_count=17))
    with pytest.raises(ValueError,match='service_identity'):verify(dict(receipt,service_identity=dict(receipt['service_identity'],pid=999)))
    (tmp_path/'response.body').write_bytes(b'changed')
    with pytest.raises(ValueError,match='source_not_ready'):verify()


def test_local_failure_diagnostic_reaches_batch_without_changing_stop_semantics():
    from app.services.dated_technical_research import safe_service_diagnostic
    data=dict(phase='local_serialization',error_type='ValidationError',upstream_status=None,api_id='unknown',physical_count=0,global_stop=False)
    assert safe_service_diagnostic(httpx.Response(502,json={'diagnostic':data}))==data
    assert safe_service_diagnostic(httpx.Response(502,json={'diagnostic':dict(data,phase='unreviewed')})) is None
