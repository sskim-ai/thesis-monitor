from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.services.unified_full_source_cohort import FreshKRSourceRunSeed
from app.services.unified_snapshot_contract import encoded
from scripts.fresh_source_only_export import (
    resolve_full_source_generation_identity, source_only_generation_preflight,
)
from scripts.kr8_fy1_continuation import source_only_projection, Kr8Continuation
from scripts.kr8_fy1_models import Kr8Execution

FIXTURE = Path(__file__).parent / 'fixtures/kr8_full_source_seed.json'


def preflight(whole, **changes):
    fields = dict(source_view_generation_id='frozen', provider_generation_id='frozen',
                  kis_generation_id='frozen')
    return source_only_generation_preflight(whole, **{**fields, **changes})


@pytest.mark.parametrize('seed', [dict(parent_run_id='frozen'),
                                      dict(parent_run_id='frozen', run_id='frozen')])
def test_current_parent_identity_and_corroborating_alias(seed):
    whole = {'seed': seed}
    original = deepcopy(whole)
    receipt = preflight(whole)
    assert receipt['generation_id'] == 'frozen' and not receipt['identity_rewritten']
    assert whole == original


@pytest.mark.parametrize('seed', [{}, {'run_id': 'frozen'}, None, [],
    {'parent_run_id': 'frozen', 'run_id': 'conflicting'},
    *[{'parent_run_id': value} for value in ('', ' ', None, 1, True, [], {})],
    *[{'parent_run_id': 'frozen', 'run_id': value} for value in ('', ' ', None, 1, True, [], {})]])
def test_missing_legacy_only_conflicting_and_invalid_identity_fail_closed(seed):
    with pytest.raises(ValueError, match='source_only_'):
        preflight({'seed': seed})


@pytest.mark.parametrize('role', ['source_view_generation_id', 'provider_generation_id', 'kis_generation_id'])
@pytest.mark.parametrize('value', ['other', '', None, 1])
def test_every_external_identity_is_required_exactly(role, value):
    with pytest.raises(ValueError, match='source_only_'):
        preflight({'seed': {'parent_run_id': 'frozen'}}, **{role: value})


def test_real_current_seed_serializer_roundtrip_enters_exact_export_preflight():
    stored = json.loads(FIXTURE.read_bytes())
    seed = FreshKRSourceRunSeed.model_validate(stored)
    # compose_full_source serializes this exact model with mode='json'.
    serialized = encoded({'seed': seed.model_dump(mode='json')})
    whole = json.loads(serialized)
    with pytest.raises(KeyError, match='run_id'):
        _ = whole['seed']['run_id']
    assert whole['seed'] == stored
    identity = resolve_full_source_generation_identity(whole)
    receipt = source_only_generation_preflight(whole, source_view_generation_id=identity,
        provider_generation_id=identity, kis_generation_id=identity)
    assert receipt['status'] == 'PASS' and receipt['generation_id'] == seed.parent_run_id


def test_exact_kr_export_entrypoint_checks_identity_before_projection():
    with pytest.raises(ValueError, match='provider_generation_mismatch'):
        source_only_projection({'seed': {'parent_run_id': 'frozen'}},
            source_view={'generation_id': 'frozen'}, provider_plan={'generation_id': 'other'},
            kis_plan={'generation_id': 'frozen'})


def test_continuation_inherits_frozen_model_and_renderer_semantics():
    for name in ('prepare', 'capture', 'verify', 'render', 'batch_topology', 'run_qualified'):
        assert getattr(Kr8Continuation, name) is getattr(Kr8Execution, name)
    assert Kr8Continuation.CALL_LIMITS == dict(market=1, core=3, **{'pass-a': 3, 'pass-b': 3})
    assert Kr8Continuation.SUBJECT_COUNT == 8 and Kr8Continuation.MARKET_SCOPES == ('kr',)
