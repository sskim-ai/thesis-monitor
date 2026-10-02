from datetime import datetime, timezone
import json

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.services.unified_class_c_owners import project_published_events, project_canonical_catalog
from app.services.unified_sealed_context import replay_publications, replay_night
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_full_source_cohort import compose_full_source
from test_unified_live_source_cohort import seed


@pytest.mark.parametrize('family', ['fed', 'canonical'])
def test_publication_owner_empty_is_not_fabricated_value(family):
    at = datetime(2026, 9, 27, tzinfo=timezone.utc)
    policy = UnifiedSourcePolicy(frozenset({'federal_reserve'}))
    engine = create_engine('sqlite://')
    SQLModel.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            value = (project_published_events(session, cutoff=at, policy=policy) if family == 'fed'
                     else project_canonical_catalog([], cutoff=at, policy=policy))
    finally:
        engine.dispose()
    raw = json.dumps(value).encode()
    params = dict(documents={'source':raw}, hashes={'source':sha256_bytes(raw)}, cutoff=at, policy=policy)
    result = replay_publications(**params)
    assert result['source']['projection'] == value
    assert not value['values'] and not value['eligible']
    params['documents']['source'] += b' '
    with pytest.raises(ValueError, match='source_hash'):
        replay_publications(**params)


def test_publication_unbound_set_is_denied():
    with pytest.raises(ValueError, match='exact_version'):
        replay_publications(documents={'new':b'{}'}, hashes={},
            cutoff=datetime.now(timezone.utc), policy=UnifiedSourcePolicy(frozenset()))


def test_whole_native_graph_requires_inventory_contract():
    with pytest.raises(ValueError, match='inventory_policy_identity'):
        compose_full_source(seed=seed(), market_inputs={}, stock_inputs={}, authority_inputs={},
            version_set={}, optional_denials={}, issuer_bridge={}, publication_inputs={}, night_inputs={})


@pytest.mark.parametrize('receipts,bodies,hashes', [([],{},{}), ([{}],{'x':b'changed'},{'x':'0'*64})])
def test_night_missing_or_changed_source_denied_before_native_owner(receipts,bodies,hashes):
    at = datetime.now(timezone.utc)
    with pytest.raises(ValueError):
        replay_night(receipts=receipts, bodies=bodies, body_hashes=hashes, observed_at=at,
            run_id='synthetic', acquisition_id='synthetic-night', expected_value_sha256='0'*64,
            policy=UnifiedSourcePolicy(frozenset({'krx_night_futures'})),
            run_started_at=at, acquisition_cutoff=at)
