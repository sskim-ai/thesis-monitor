"""Synthetic only: original Intake issuer, immutable receipts, no live claims."""
from dataclasses import replace, FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

import httpx
import pytest

from app.services import dated_capture_research as bridge
from app.services import prospective_class_c_owner as registration
from app.services.public_capture_storage import FileCaptureArchive
from app.services.vnext_public_capture import public_descriptor
from app.services.vnext_research_store import digest, encoded, ResearchStore
from app.services.vnext_composite_research import CompositeView
from test_c8_source_intake import pending
from test_minimal_class_c_export import POLICY


@pytest.fixture
def prepared(tmp_path):
    approval, capture, owner, receipt = pending(tmp_path)
    security = registration.source_intake_snapshot(owner, generation_id='C8_TEST',
        subjects=('NEWUS',), policy=POLICY)[0]['NEWUS']
    at = datetime.now(timezone.utc).isoformat()
    archive = FileCaptureArchive(tmp_path/'archive', run_id='SYNTHETIC', started_at=at,
        securities=[security], code_pins={}, enabled=True)
    for endpoint, payload in [('profile2', dict(ticker='NEWUS', exchange='NASDAQ', currency='USD',
        name=security.get('company_name') or 'Synthetic')),
        ('metric', dict(symbol='NEWUS', metric=dict(peTTM=12, pbQuarterly=2, forwardPE=10)))]:
        request = httpx.Request('GET', 'https://finnhub.io/api/v1/stock/'+endpoint,
            params=dict(symbol='NEWUS', **({'metric':'all'} if endpoint=='metric' else {})))
        descriptor = public_descriptor(request); raw = encoded(payload)
        at = datetime.now(timezone.utc).isoformat()
        archive.capture('SYNTHETIC','Finnhub',digest(descriptor),raw,
            dict(provider='Finnhub',run_id='SYNTHETIC',raw_sha256=digest(raw),
                raw_birth='CURRENT_HTTP',status=200,started_at=at,captured_at=at,
                response_headers={},request=descriptor))
    seal = archive.seal_captures()
    args = dict(root=archive.path.parent, manifest_sha256=archive.manifest_sha256,
        capture_seal_sha256=seal, run_id='SYNTHETIC', ticker='NEWUS',
        canonical_security_id=security['canonical_security_id'],
        as_of=datetime.now(timezone.utc).isoformat())
    bundle = bridge.bind_dated_archive(**args,enabled=True)
    return archive,bundle,owner,receipt,args


def test_default_off_and_immutable_locator(prepared):
    archive,bundle,owner,receipt,args=prepared
    with pytest.raises(ValueError,match='enable'):bridge.bind_dated_archive(**args)
    with pytest.raises(ValueError,match='enable'):CompositeView.from_dated_archive(bundle)
    with pytest.raises(FrozenInstanceError):bundle.run_id='OTHER'


def test_genuine_pending_owner_reference_without_sql_write(prepared,monkeypatch):
    archive,bundle,owner,receipt,args=prepared
    before={str(p):digest(p.read_bytes()) for p in archive.path.parent.rglob('*') if p.is_file()}
    def denied(*a,**k):raise AssertionError('SQL_CONNECTION_NOT_ALLOWED')
    monkeypatch.setattr(sqlite3,'connect',denied)
    view=CompositeView.from_dated_archive(bundle,enabled=True)
    packet=view.packet_pending_research(ticker='NEWUS',owner=owner,generation_id='C8_TEST',policy=POLICY)
    assert packet['registration_status']=='GENUINE_INTAKE_RESEARCH_ONLY'
    assert not packet['strict_ready'] and not packet['send'] and packet['model']=='OFF'
    assert not packet['source_generation_reissued']
    for row in packet['evidence']:
        assert row['data']['overall_direction_use'] is False
        assert row['original_run']=='SYNTHETIC'
        assert row['provenance']['receipt_sha256']
    after={str(p):digest(p.read_bytes()) for p in archive.path.parent.rglob('*') if p.is_file()}
    assert before==after


@pytest.mark.parametrize('change',['bare','expired','generation','ticker','security'])
def test_pending_invalid_original_owner_denied(prepared,monkeypatch,change):
    archive,bundle,owner,receipt,args=prepared
    view=CompositeView.from_dated_archive(bundle,enabled=True)
    if change=='bare':owner=registration.SourceIntakeOwner()
    if change=='expired':monkeypatch.setattr(registration,'_now',lambda:datetime.fromisoformat(receipt['expires_at']))
    if change=='security':view.identities['NEWUS']['canonical_security_id']='OTHER'
    with pytest.raises(ValueError):
        view.packet_pending_research(ticker='OTHER' if change=='ticker' else 'NEWUS',
            owner=owner,generation_id='OTHER' if change=='generation' else 'C8_TEST',policy=POLICY)


@pytest.mark.parametrize('change',['run_id','ticker','canonical_security_id','manifest_sha256','capture_seal_sha256'])
def test_locator_tamper_denied(prepared,change):
    _,bundle,*_=prepared
    with pytest.raises(ValueError):
        CompositeView.from_dated_archive(replace(bundle,**{change:'0'*64}),enabled=True)


def test_raw_tamper_after_bind_denied(prepared):
    archive,bundle,*_=prepared
    view=CompositeView.from_dated_archive(bundle,enabled=True)
    next((archive.path.parent/'raw').iterdir()).write_bytes(b'{}')
    with pytest.raises(ValueError):view.packet('NEWUS')


def test_original_projection_matches_composite_fields(prepared):
    _,bundle,*_=prepared
    _,_,snapshots,_=bridge._replay(bundle)
    packet=CompositeView.from_dated_archive(bundle,enabled=True).packet('NEWUS')
    actual={r['data']['metric']:r['data'] for r in packet['evidence']}
    assert actual=={s.metric:s.model_dump(mode='json') for s in snapshots}
    forward=actual['FORWARD_PE']
    assert forward['horizon_authority']=='USER_AUTHORIZED_PRODUCT_POLICY'
    assert not forward['core_visibility'] and not forward['pass_a_visibility']
    assert not any(r['field']=='valuation.FY1_EPS' for r in packet['evidence'])


def test_original_pending_denials_and_active_packet_unchanged(tmp_path):
    path=tmp_path/'fixture.sqlite3'
    with sqlite3.connect(path) as c:
        c.executescript('CREATE TABLE watchlistitem(ticker TEXT,active INTEGER);'
            'CREATE TABLE research_run(run_id TEXT,as_of TEXT);'
            'CREATE TABLE source_capture(run_id TEXT,raw_sha TEXT);'
            'CREATE TABLE research_observation(field TEXT,status TEXT,source_sha TEXT,payload_json TEXT,run_id TEXT,ticker TEXT);'
            "INSERT INTO watchlistitem VALUES('NEWUS',0);"
            "INSERT INTO research_run VALUES('SYNTHETIC','2026-11-06T00:00:00+00:00');")
    store=object.__new__(ResearchStore);store.path=path
    with pytest.raises(ValueError,match='not_registered'):store.packet('SYNTHETIC','NEWUS')
    with pytest.raises(ValueError,match='not_registered'):
        store.observation('SYNTHETIC','NEWUS','valuation.PER','SOURCE_REFERENCE','a'*64,dict(strict_native=False))
    with sqlite3.connect(path) as c:c.execute('UPDATE watchlistitem SET active=1')
    assert store.packet('SYNTHETIC','NEWUS')['live_authority'] is False


def test_absent_page_without_selection_proof_denied(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from app.services import retained_identity_routing as routing
    root=tmp_path/'routing';root.mkdir();(root/'plan.json').write_text('{}')
    descriptor=SimpleNamespace(endpoint_operation='ka10099',logical_request_id='unrequested',raw_path='absent',response_binding=None)
    monkeypatch.setattr(routing,'decode_request_plan',lambda _:SimpleNamespace(descriptors=(descriptor,)))
    monkeypatch.setattr(routing,'consume_bound_result',lambda **kw:pytest.fail('unrequested receipt consumed'))
    with pytest.raises(ValueError,match='selected_receipt_missing'):
        routing.retained_listing_rows(root)


def test_projection_mutation_and_missing_registry_denied(prepared):
    _,bundle,*_=prepared
    view=CompositeView.from_dated_archive(bundle,enabled=True)
    with pytest.raises(ValueError,match='balanced_live_use_registry_required'):
        view.unified_premodel(registry=None)
    view.rows=()
    with pytest.raises(ValueError,match='dated_projection_changed'):view.packet('NEWUS')


def test_original_production_fresh_generation_still_denied():
    from app.services.canonical_source_composition import validate_fresh_context_generation
    from app.services.unified_source_policy import UnifiedSourcePolicy
    policy=UnifiedSourcePolicy(frozenset({'finnhub'}))
    with pytest.raises(ValueError,match='fresh_context_generation_or_policy_mismatch'):
        validate_fresh_context_generation(dict(run_id='OLD',run_started_at='OLD',policy=policy),
            parent_run_id='NEW',started_at='NEW',source_policy_sha256=digest(sorted(policy.allowed_providers)))


def test_original_registry_and_catalog_premodel_reference_only(prepared):
    from app.services.vnext_daily_research import UseRegistry
    _,bundle,*_=prepared
    view=CompositeView.from_dated_archive(bundle,enabled=True)
    registry=UseRegistry()
    packet=view.unified_premodel(registry=registry)
    assert packet['valuation_facts']
    assert not packet['strict_ready'] and not packet['send']
    assert all('OVERALL' not in e['candidate_decision_axis'] for e in packet['admissibility'])
    for e in packet['base']['evidence']:
        registry.revoke(bundle.canonical_security_id,e['source_sha'],source_generation=bundle.run_id)
    denied=view.unified_premodel(registry=registry)
    assert not denied['valuation_facts']
    assert not any(e['eligible'] for e in denied['admissibility'])
