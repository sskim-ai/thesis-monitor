"""Changed hot paths only; synthetic registration, never live Source authority."""
from datetime import datetime, timezone
import json
from pathlib import Path
import socket
import sqlite3
import sqlite3.dbapi2
import time
from types import SimpleNamespace
from urllib.parse import unquote, urlsplit

import pytest

from app.services import campaign_runtime_cap as runtime
from app.services import minimal_class_c_export as capture_export
from app.services import prospective_class_c_owner as registration
from app.services import selected_source_dispatch as dispatch
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_class_c_owners import LOCAL_ROLES
from tests import test_c22ad_lifecycle as registration_fixture
from tests.test_c22ad_lifecycle import capture, POLICY
from tests.test_c22ai_runtime_cap import ledger, reserve


@pytest.fixture(autouse=True)
def offline_only(monkeypatch, tmp_path):
    anchor = datetime.now(timezone.utc)

    class TestClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return anchor.astimezone(tz) if tz else anchor.replace(tzinfo=None)

    monkeypatch.setattr(registration_fixture, 'datetime', TestClock)
    monkeypatch.setattr(capture_export, 'datetime', TestClock)
    monkeypatch.setattr(registration, '_now', lambda: anchor)
    def denied(*args, **kwargs):
        raise AssertionError('throughput_test_external_network_denied')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)
    original = sqlite3.connect

    def local_database(path, *args, **kwargs):
        value = str(path)
        if value != ':memory:':
            target = Path(unquote(urlsplit(value).path) if value.startswith('file:') else value)
            assert target.resolve().is_relative_to(tmp_path.resolve()), 'operating_database_denied'
        return original(path, *args, **kwargs)
    monkeypatch.setattr(sqlite3, 'connect', local_database)
    monkeypatch.setattr(sqlite3.dbapi2, 'connect', local_database)


@pytest.fixture
def guard(tmp_path):
    _, _, _, _, (_, owners, _) = capture(tmp_path)
    owner = owners['us']
    _, receipt = registration._state(owner)
    stock = SimpleNamespace(run_id=receipt['generation_id'], market='us',
        frozen_at=datetime.fromisoformat(receipt['cutoff']), subjects=tuple(receipt['bindings']),
        reads=(SimpleNamespace(latest_completed_session=receipt['calendar']['target']),))
    wire = object.__new__(dispatch.SelectedSourceDispatcher)
    wire.guard = lambda: None
    wire.registration_owner, wire.stock, wire.policy = owner, stock, POLICY
    # Exercise the existing constructor's qualification boundary without
    # claiming a Worker/normalizer/financial Source admission.
    wire._require_current()
    wire._qualified_registration = (owner, stock, POLICY)
    return wire, receipt


def test_single_projection_then_original_live_guard_without_memory_db_rebuild(guard, monkeypatch):
    from app.services import unified_local_seed_bridge as bridge
    wire, _ = guard
    full, cheap, connections = [], [], []
    original_seed = dispatch.local_seed
    original_check = registration.require_generation
    original_engine = bridge.create_engine

    def observed_engine(url, *args, **kwargs):
        connections.append(str(url))
        return original_engine(url, *args, **kwargs)

    def observed_check(*args, **kwargs):
        cheap.append(1)
        return original_check(*args, **kwargs)

    monkeypatch.setattr(bridge, 'create_engine', observed_engine)
    monkeypatch.setattr(registration, 'require_generation', observed_check)
    before = time.perf_counter()
    for _ in range(3):
        original_seed(wire.registration_owner, stock=wire.stock, policy=wire.policy)
    full_seconds = time.perf_counter()-before
    old_memory = connections.count('sqlite://')
    connections.clear()
    cheap.clear()
    monkeypatch.setattr(dispatch, 'local_seed', lambda *a, **k: full.append(1))
    before = time.perf_counter()
    for _ in range(3):
        wire._require_current()
    cheap_seconds = time.perf_counter()-before
    assert not full and len(cheap) == 3 and not connections
    assert old_memory == 3*len(LOCAL_ROLES) and old_memory > 0
    print(json.dumps(dict(benchmark='SYNTHETIC_LOCAL_GUARD_ONLY_NOT_LIVE',
        calls=3,old_memory_databases=old_memory,new_memory_databases=0,
        old_seconds=full_seconds,new_seconds=cheap_seconds)))


@pytest.mark.parametrize('failure', ['revoked', 'expired'])
def test_original_owner_revoke_and_expiry_still_block(guard, monkeypatch, failure):
    wire, receipt = guard
    if failure == 'revoked':
        registration.revoke_prospective_owner(wire.registration_owner)
        expected = 'live_backend_owner'
    else:
        monkeypatch.setattr(registration, '_now', lambda: datetime.fromisoformat(receipt['expires_at']))
        expected = 'owner_expired'
    with pytest.raises(ValueError, match=expected):
        wire._require_current()


@pytest.mark.parametrize('field', ['registration_owner', 'stock', 'policy'])
def test_frozen_registration_context_cannot_be_rebound(guard, field):
    wire, _ = guard
    replacement = UnifiedSourcePolicy(POLICY.allowed_providers) if field == 'policy' else object()
    setattr(wire, field, replacement)
    with pytest.raises(SourceSafetyStop, match='registration_scope_changed'):
        wire._require_current()


def test_identity_hashed_once_but_every_row_and_chain_still_verified(tmp_path, monkeypatch):
    journal = ledger(tmp_path)
    cap = runtime.RuntimeCap(journal.worker_binding())
    key = reserve(cap, 'SYNTHETIC')
    cap.dispatched(key)
    cap.finish(key, status=200)
    raw = journal.path.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    identity, calls = rows[0]['identity'], []
    original = runtime.digest

    def counted(value):
        calls.append('identity' if value == identity else 'row')
        return original(value)
    monkeypatch.setattr(runtime, 'digest', counted)
    assert cap.state()['total'] == 1
    assert calls.count('identity') == 1 and calls.count('row') == len(rows)
    for case in ('first_identity', 'later_identity', 'value', 'previous', 'sequence'):
        changed = json.loads(json.dumps(rows))
        if case == 'first_identity':
            changed[0]['identity']['max_http'] += 1
        elif case == 'later_identity':
            changed[-1]['identity']['max_http'] += 1
        elif case == 'value':
            changed[-1]['value']['status'] = 429
        elif case == 'previous':
            changed[-1]['previous'] = '0'*64
        else:
            changed[-1]['sequence'] += 1
        journal.path.write_bytes(b'\n'.join(runtime.encoded(row) for row in changed)+b'\n')
        with pytest.raises(ValueError, match='CHAIN_DRIFT'):
            cap.state()
    journal.path.write_bytes(raw)


def test_caps_and_stop_are_not_refilled_by_optimized_reads(tmp_path):
    journal = ledger(tmp_path, maximum=1)
    cap = runtime.RuntimeCap(journal.worker_binding())
    key = reserve(cap, 'SYNTHETIC')
    cap.dispatched(key)
    cap.finish(key, status=200)
    with pytest.raises(ValueError, match='CAP_EXHAUSTED'):
        reserve(cap, 'OTHER_SYNTHETIC')
    assert cap.state()['total'] == 1
    journal.stop('SYNTHETIC_TEST_STOP')
    with pytest.raises(ValueError, match='EXPIRED_OR_STOPPED'):
        cap.require_current()


def test_torn_journal_is_still_rejected(tmp_path):
    journal = ledger(tmp_path)
    cap = runtime.RuntimeCap(journal.worker_binding())
    with journal.path.open('ab') as stream:
        stream.write(b'{')
    with pytest.raises(ValueError, match='MISSING_OR_TORN'):
        cap.state()
