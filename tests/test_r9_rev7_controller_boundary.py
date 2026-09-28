from copy import deepcopy
import json

import pytest

from app.services.unified_full_source_cohort import FullSourceRunSeed, FreshFullSourceRunSeed, compose_full_source
from app.services.unified_live_source_transport import BoundedTransport
from app.services.unified_snapshot_contract import digest
from app.services.unified_run_artifacts import sha256_bytes
from scripts.r2b_r9_full_fresh_requalification import _read, assemble_current_stocks
from tests.test_unified_live_source_cohort import seed


def test_legacy_seed_bytes_not_extended_and_fresh_seed_exact_hash():
    old = seed()
    assert 'fresh_stock_owner_set_sha256' not in old.model_dump(mode='json')
    assert FullSourceRunSeed.model_validate_json(old.model_dump_json()).sha256 == old.sha256
    new = FreshFullSourceRunSeed(**old.model_dump(), fresh_stock_owner_set_sha256='a'*64)
    assert new.sha256 != old.sha256
    assert FreshFullSourceRunSeed.model_validate_json(new.model_dump_json()).sha256 == new.sha256
    with pytest.raises(ValueError):
        FreshFullSourceRunSeed(**old.model_dump(), fresh_stock_owner_set_sha256='')


@pytest.mark.parametrize('key', ['publication_inputs', 'night_inputs'])
def test_fresh_seed_cannot_adopt_old_publication_replay(key):
    new = FreshFullSourceRunSeed(**seed().model_dump(), fresh_stock_owner_set_sha256='a'*64)
    args = dict(seed=new, market_inputs={}, stock_inputs={}, authority_inputs={},
                version_set={}, optional_denials={}, issuer_bridge={}, **{key:{}})
    with pytest.raises(ValueError, match='fresh_whole_context_replay_not_closed'):
        compose_full_source(**args)


@pytest.mark.parametrize('value', [{}, {'CORZ':{}}])
def test_controller_cannot_run_selective_current_subset(tmp_path, value):
    with pytest.raises(ValueError, match='exact_all22'):
        assemble_current_stocks(tmp_path, {'stocks':value})


def test_artifact_hash_and_symlink_boundaries(tmp_path):
    path = tmp_path / 'source.json'
    path.write_bytes(b'{}')
    binding = dict(path='source.json', sha256=sha256_bytes(b'{}'))
    assert _read(tmp_path, binding) == b'{}'
    for name in ('../source.json', '/tmp/source.json'):
        with pytest.raises(ValueError, match='relative_artifact'):
            _read(tmp_path, {**binding, 'path':name})
    (tmp_path/'link.json').symlink_to(path)
    with pytest.raises(ValueError, match='symlink'):
        _read(tmp_path, {**binding, 'path':'link.json'})
    path.write_bytes(b'{"mutated":true}')
    with pytest.raises(ValueError, match='hash_mismatch'):
        _read(tmp_path, binding)


def test_macro_query_and_ecos_path_credentials_never_enter_plan_receipts(tmp_path):
    wire = BoundedTransport(root=tmp_path, maximum_logical=2, guard=lambda:None, secrets=('very-private-key',))
    requests = [dict(route='/fred/series/observations', query={'api_key':'very-private-key', 'series_id':'DGS10'}),
                dict(route='/api/KeyStatisticList/very-private-key/json/kr/1/100', query={})]
    for request in requests:
        original = deepcopy(request)
        row = wire.begin(request)
        assert request == original
        assert row['request_sha256'] == digest(row['request'])
    payload = b''.join(p.read_bytes() for p in tmp_path.iterdir())
    assert b'very-private-key' not in payload
    assert b'DGS10' in payload and b'[REDACTED]' in payload
    assert all(json.loads(p.read_bytes())['secret_exchange'] is False for p in tmp_path.iterdir())
