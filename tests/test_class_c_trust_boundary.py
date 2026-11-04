"""Synthetic immutable-export mechanics, never a real registration authority."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from types import SimpleNamespace

import pytest

from app.services.canonical_source_replay import current_local_seed
from app.services.fresh_source_run_contract import validate_local_seed
from app.services.unified_local_seed_bridge import admit_pinned_local_seed, local_owner
from app.services.unified_snapshot_contract import digest, encoded
from test_unified_stock_owner import source as source_fixture


@pytest.fixture
def frozen_source():
    source = source_fixture.__wrapped__()
    document = source['local_seed']
    raw = encoded(document)
    return source, document, raw, sha256(raw).hexdigest()


def admit(fixture, raw=None, **overrides):
    source, document, original, pin = fixture
    args = dict(expected_sha256=pin, market='us', session_key='2026-09-25',
        cutoff=source['plan'].frozen_at, subjects=document['universe']['eligible_subjects'],
        policy=source['policy'])
    args.update(overrides)
    return admit_pinned_local_seed(original if raw is None else raw, **args)


def rehash_records(document):
    for part in document['roles'].values():
        for row in part['records']:
            if row['table'] != 'watchlistitem':
                row['original_record_sha256'] = digest(row['record'])
        part['version'] = digest(part['records'])


def replay(document, source):
    return [local_owner(role=role, market='us', session_key='2026-09-25',
        policy=source['policy']).project_and_validate(encoded(document), source['plan'].frozen_at)
        for role in document['roles']]


def test_independent_pin_and_original_owner_replay_preserve_config_only(frozen_source):
    _, document, _, _ = frozen_source
    before = deepcopy(document)
    assert admit(frozen_source) == before
    assert document == before
    assert document['production_seed_qualified'] is False
    assert all(r['source_receipt'] is None for r in document['roles'].values())


@pytest.mark.parametrize('case', ['cutoff', 'original_digest', 'country', 'thesis_v2', 'thesis_v3',
    'issuer', 'security', 'role_omission', 'current_flag', 'clearance_flag'])
def test_rehashed_caller_replacement_cannot_replace_frozen_export(frozen_source, case):
    _, document, _, _ = frozen_source
    d = deepcopy(document)
    security = d['roles']['security_identity']['records'][0]
    thesis = d['roles']['stored_thesis_and_business_metadata']['records'][0]
    if case == 'cutoff':
        d['cutoff'] = '2000-01-01T00:00:00+00:00'
    elif case == 'original_digest':
        security['original_record_sha256'] = '0' * 64
    elif case == 'country':
        security['record']['country'] = 'KR'
    elif case.startswith('thesis_v'):
        thesis['record']['version'] = int(case[-1])
        thesis['record']['core_thesis'] = 'Different user configuration'
    elif case == 'issuer':
        security['record']['canonical_company_id'] = 'wrong-issuer'
    elif case == 'security':
        security['record']['canonical_security_id'] = 'wrong-security'
    elif case == 'role_omission':
        d['roles'].pop('security_identity')
    else:
        d[case] = True
    for part in d['roles'].values():
        part['version'] = digest(part['records'])
    with pytest.raises(ValueError, match='independent_source_pin'):
        admit(frozen_source, encoded(d))


@pytest.mark.parametrize('roles', [{}, {'universe': {'records': [], 'eligible': False}}])
def test_ng02_roles0_roles1_rejected(roles):
    with pytest.raises(ValueError, match='required_roles'):
        validate_local_seed(dict(contract='unified-local-seed-projection-v1', denials=[], roles=roles))


@pytest.mark.parametrize('field,value', [('exchange', 'KOSPI'), ('exchange', 'UNSUPPORTED'),
    ('exchange', 'NYSE')])
def test_ng02_wrong_exchange_even_with_recomputed_record_hash(frozen_source, field, value):
    source, d, _, _ = frozen_source
    d['roles']['security_identity']['records'][0]['record'][field] = value
    rehash_records(d)
    with pytest.raises(ValueError):
        replay(d, source)


def test_ng02_declared_cutoff_has_inner_consistency_and_outer_pin(frozen_source):
    source, d, _, _ = frozen_source
    d['cutoff'] = '2000-01-01T00:00:00+00:00'
    with pytest.raises(ValueError, match='cutoff'):
        replay(d, source)
    with pytest.raises(ValueError, match='independent_source_pin'):
        admit(frozen_source, encoded(d))


@pytest.mark.parametrize('table', ['securitymaster', 'watchlistitem'])
def test_original_record_digest_requires_external_pin_for_projected_rows(frozen_source, table):
    source, d, _, _ = frozen_source
    for part in d['roles'].values():
        for row in part['records']:
            if row['table'] == table:
                row['original_record_sha256'] = '0' * 64
        part['version'] = digest(part['records'])
    if table == 'securitymaster':
        with pytest.raises(ValueError, match='original_record_digest'):
            replay(d, source)
    else:
        # Full Watchlist content is deliberately omitted; replay cannot invent it.
        assert all(p.eligible for p in replay(d, source))
    with pytest.raises(ValueError, match='independent_source_pin'):
        admit(frozen_source, encoded(d))


@pytest.mark.parametrize('cycle', ['2026-09-24', '2026-09-25', '2026-09-26'])
def test_ng02_first_eligible_requires_explicit_cycle_session_authority(frozen_source, cycle):
    source, d, _, _ = frozen_source
    d['roles']['universe']['records'][0]['record']['first_eligible_session'] = cycle
    rehash_records(d)
    with pytest.raises(ValueError, match='first_eligible_cycle_to_session_authority_required'):
        replay(d, source)


@pytest.mark.parametrize('issuer_type,security_type,country', [
    ('domestic_us', 'common_stock', 'US'), ('foreign_private_issuer', 'adr', 'KR'),
    ('foreign_private_issuer', 'ads', 'TW'), ('etf', 'etf', 'US')])
def test_listing_not_issuer_domicile_and_no_per_share_grant(frozen_source, issuer_type, security_type, country):
    source, d, _, _ = frozen_source
    record = d['roles']['security_identity']['records'][0]['record']
    record.update(issuer_type=issuer_type, security_type=security_type, country=country)
    rehash_records(d)
    assert all(p.eligible for p in replay(d, source))
    assert record['adr_ratio'] is None
    assert d['production_seed_qualified'] is False
    if encoded(d) == frozen_source[2]:
        assert admit(frozen_source, encoded(d)) == d
    else:
        with pytest.raises(ValueError, match='independent_source_pin'):
            admit(frozen_source, encoded(d))


@pytest.mark.parametrize('issuer_type,security_type', [('domestic_us', 'ads'),
    ('krx', 'adr'), ('adr', 'common_stock')])
def test_existing_identity_conflicts_rejected_even_after_rehash(frozen_source, issuer_type, security_type):
    source, d, _, _ = frozen_source
    d['roles']['security_identity']['records'][0]['record'].update(
        issuer_type=issuer_type, security_type=security_type)
    rehash_records(d)
    with pytest.raises(ValueError):
        replay(d, source)


def test_venue_alias_is_only_structural_compatibility(frozen_source):
    source, d, _, _ = frozen_source
    d['roles']['security_identity']['records'][0]['record']['exchange'] = 'NYSE_ARCA'
    d['roles']['universe']['records'][0]['record']['exchange'] = 'ARCA'
    rehash_records(d)
    assert all(p.eligible for p in replay(d, source))
    with pytest.raises(ValueError, match='independent_source_pin'):
        admit(frozen_source, encoded(d))


@pytest.mark.parametrize('market,session_key,cutoff,eligible', [
    ('us', '2026-11-26', '2026-11-27T00:00:00+00:00', False),
    ('us', '2026-11-27', '2026-11-27T17:59:00+00:00', False),
    ('us', '2026-11-27', '2026-11-27T18:00:00+00:00', True),
    ('us', '2026-03-09', '2026-03-09T19:59:00+00:00', False),
    ('us', '2026-03-09', '2026-03-09T20:00:00+00:00', True),
    ('kr', '2026-03-02', '2026-03-03T00:00:00+00:00', False),
    ('kr', '2026-03-03', '2026-03-03T06:29:00+00:00', False),
    ('kr', '2026-03-03', '2026-03-03T06:30:00+00:00', True)])
def test_actual_calendar_no_weekday_fallback(market, session_key, cutoff, eligible):
    from sqlmodel import Session, SQLModel, create_engine
    from app.services.unified_persisted_projection import project_local_seed
    from app.services.unified_source_policy import UnifiedSourcePolicy
    engine = create_engine('sqlite://')
    try:
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            args = dict(market=market, session_key=session_key, cutoff=datetime.fromisoformat(cutoff),
                policy=UnifiedSourcePolicy(frozenset({'canonical_local'})))
            if eligible:
                result = project_local_seed(session, **args)
                assert not any(r['eligible'] for r in result['roles'].values())
            else:
                with pytest.raises(ValueError, match='local_session_eligibility_unproven'):
                    project_local_seed(session, **args)
    finally:
        engine.dispose()


def test_unavailable_calendar_denies_before_owner_reads(monkeypatch):
    import app.services.unified_persisted_projection as projection
    from app.services.unified_source_policy import UnifiedSourcePolicy
    monkeypatch.setattr(projection, '_exchange_session_close', lambda *args: None)
    with pytest.raises(ValueError, match='local_session_eligibility_unproven'):
        projection.project_local_seed(SimpleNamespace(new=[], dirty=[], deleted=[]),
            market='us', session_key='2026-09-25', cutoff=datetime(2026, 9, 28, tzinfo=timezone.utc),
            policy=UnifiedSourcePolicy(frozenset({'canonical_local'})))


@pytest.mark.parametrize('case', ['missing', 'wrong', 'late_cutoff', 'market', 'session', 'cohort'])
def test_unavailable_or_inconsistent_authority_denied(frozen_source, case):
    kwargs = {'missing': {'expected_sha256': None}, 'wrong': {'expected_sha256': 'f'*64},
        'late_cutoff': {'cutoff': frozen_source[0]['plan'].frozen_at + timedelta(seconds=1)},
        'market': {'market': 'kr'}, 'session': {'session_key': '2026-09-24'},
        'cohort': {'subjects': ['UNSEEN']}}[case]
    with pytest.raises(ValueError):
        admit(frozen_source, **kwargs)


@pytest.fixture
def canonical_input(tmp_path, frozen_source):
    source, d, raw, pin = frozen_source
    path = tmp_path / 'class-c/local-us.json'
    path.parent.mkdir()
    path.write_bytes(raw)
    plan = SimpleNamespace(run_id='synthetic-export-replay', frozen_at=source['plan'].frozen_at,
        universe={'us': d['universe']['eligible_subjects']},
        reads=[SimpleNamespace(market='us', latest_completed_session='2026-09-25')])
    frozen = dict(generation_id=plan.run_id, frozen_at=plan.frozen_at.isoformat(),
        sessions={'us': '2026-09-25'}, protected_input_hashes={'class-c/local-us.json': pin})
    return tmp_path, frozen, plan, source['policy'], path


@pytest.mark.parametrize('case', ['valid', 'missing_pin', 'changed_bytes', 'generation', 'session', 'cutoff', 'symlink'])
def test_actual_canonical_local_consumer_uses_prefrozen_hash(canonical_input, case):
    root, frozen, plan, policy, path = canonical_input
    if case == 'valid':
        assert current_local_seed(root, frozen, plan, 'us', policy)['production_seed_qualified'] is False
        return
    if case == 'missing_pin':
        frozen['protected_input_hashes'] = {}
    elif case == 'changed_bytes':
        path.write_bytes(path.read_bytes() + b' ')
    elif case == 'generation':
        frozen['generation_id'] = 'other'
    elif case == 'session':
        frozen['sessions']['us'] = '2026-09-24'
    elif case == 'cutoff':
        frozen['frozen_at'] = (plan.frozen_at + timedelta(seconds=1)).isoformat()
    else:
        target = root / 'original.json'
        path.rename(target)
        path.symlink_to(target)
    with pytest.raises(ValueError):
        current_local_seed(root, frozen, plan, 'us', policy)


def test_actual_stock_inputs_cannot_bypass_local_gate(canonical_input, monkeypatch):
    import app.services.canonical_source_replay as replay_module
    import app.services.completed_price_state as price_module
    root, frozen, plan, policy, path = canonical_input
    plan.reads[0].subject = 'CORZ'
    plan.contract = 'one-shot-stock-source-acquisition-v1'
    frozen['stock_plan'] = {}
    frozen['plan'] = {}
    frozen['protected_input_hashes'] = {}
    (root / 'native').mkdir()
    (root / 'native/raw-owner-replay.json').write_bytes(encoded([{'status': 'PASS'}]))
    monkeypatch.setattr(replay_module, 'StockPlan', SimpleNamespace(model_validate=lambda _: plan))
    monkeypatch.setattr(replay_module, 'decode_request_plan', lambda _: None)
    monkeypatch.setattr(price_module, 'require_plan', lambda *args: None)
    accepted, errors = replay_module.stock_inputs(root, frozen, policy,
        {'logical_results': {}, 'completed_at': frozen['frozen_at']})
    assert not accepted
    assert 'independent_freeze_pin_missing' in errors['CORZ']['reason']


@pytest.mark.parametrize('cycle', ['2026-09-24', '2026-09-25', '2026-09-26'])
def test_canonical_preserves_cycle_authority_gap(canonical_input, cycle):
    import json
    root, frozen, plan, policy, path = canonical_input
    document = json.loads(path.read_bytes())
    document['roles']['universe']['records'][0]['record']['first_eligible_session'] = cycle
    rehash_records(document)
    raw = encoded(document)
    path.write_bytes(raw)
    # Synthetic trusted-export variation tests semantics, not real issuance.
    frozen['protected_input_hashes']['class-c/local-us.json'] = sha256(raw).hexdigest()
    with pytest.raises(ValueError, match='first_eligible_cycle_to_session_authority_required'):
        current_local_seed(root, frozen, plan, 'us', policy)
