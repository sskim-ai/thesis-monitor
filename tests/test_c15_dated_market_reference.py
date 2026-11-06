"""Synthetic boundary tests are not real Market Owner acceptance."""
import hashlib
import json
import pytest
from app.services import dated_market_component_reference as reference
from app.services.unified_snapshot_contract import digest


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    from app.services import market_component_execution
    root=tmp_path/'kr';root.mkdir()
    dispatch=root/'dispatch';dispatch.mkdir()
    market=root/'kr-market';market.mkdir()
    value={'observations':[], 'missing_reads':['INDEX:ka20009']}
    raw=json.dumps(value).encode();(market/'aggregate-value.json').write_bytes(raw)
    receipt=dict(artifact_sha256=hashlib.sha256(raw).hexdigest(),run_id='TEST_ONLY',market='kr',session='2026-11-06')
    (market/'aggregate.json').write_text(json.dumps(receipt))
    bundle=dict(market='kr',root=str(dispatch),cutoff='2026-11-06T10:00:00+00:00',
        owner_proof={'value_sha256':digest(value)})
    p=root/'bundle.json';p.write_text(json.dumps(bundle))
    monkeypatch.setattr(market_component_execution,'cold_component',lambda b:dict(
        generation_id='TEST_ONLY',component_sha256='a'*64,status='TEST_ONLY_ORIGINAL_COLD_STUB'))
    return p,hashlib.sha256(p.read_bytes()).hexdigest(),market


def test_default_off_does_not_read_files():
    with pytest.raises(ValueError,match='disabled'):
        reference.read_dated_component('/not/read',expected_sha256='0'*64)


def test_reference_preserves_dates_missing_roles_and_no_authority(fixture):
    p,sha,_=fixture
    result=reference.read_dated_component(p,expected_sha256=sha,enabled=True)
    assert result['completed_session']=='2026-11-06'
    assert result['value']['missing_reads']==['INDEX:ka20009']
    assert result['new_owner_issued'] is False
    assert 'NOT a sealed research Market context' in reference.render_reference(result)


def test_changed_bundle_rejected(fixture):
    p,sha,_=fixture;p.write_text('{}')
    with pytest.raises(ValueError,match='hash_mismatch'):
        reference.read_dated_component(p,expected_sha256=sha,enabled=True)


def test_changed_aggregate_rejected(fixture):
    p,sha,market=fixture;(market/'aggregate-value.json').write_text('{}')
    with pytest.raises(ValueError,match='value_binding'):
        reference.read_dated_component(p,expected_sha256=sha,enabled=True)


@pytest.mark.parametrize('field',['economic_use','full_market_parent','send','sealed_research_market_context'])
def test_renderer_cannot_promote_reference(fixture,field):
    p,sha,_=fixture
    result=reference.read_dated_component(p,expected_sha256=sha,enabled=True);result[field]=True
    with pytest.raises(ValueError,match='scope_or_hash'):
        reference.render_reference(result)
