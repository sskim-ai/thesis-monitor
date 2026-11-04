"""TEST_ONLY projection/lifetime proofs, not independently owned issuer evidence."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from app.services import accepted_decision_v2_runtime_service as runtime
from app.services import legacy_context_authority as authority
from app.services.business_delta_evidence_service import build_business_delta_evidence_view
from app.services.canonical_monitoring_input import subject_inputs
from app.services.canonical_monitoring_time import reproject_time
from app.services.canonical_source_inputs import fresh_authority_inputs
from app.services.canonical_subject_preflight import preflight_subject
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from app.services.direction_timing_ownership_service import (
    DirectionalCoreCandidate, EvidenceDomain, OwnedEvidencePacket,
    build_owned_evidence_packet, stage_alias_catalogs, technical_feature_inventory,
    validate_directional_core_ownership, verified_owned_packet_view,
)
from app.services.logical_condition_service import LogicalSeverity, source_logical_condition
from app.services.fundamental_input_policy import fundamental_ref_projection, price_availability
from app.services.market_expectation_evidence_service import build_market_expectation_evidence_view
from app.services.structured_autonomy_alias_service import build_evidence_alias_catalog
from scripts.directional_core_price_timing_holdout import _owned_context
from tests.test_core_input_source_isolation_r21 import (
    _financial_stock, _isolated_data as _isolated_data, _native, _packet,
)
from tests.test_direction_timing_ownership_service import _core


def _fixture(ticker='UNSEEN_US_R22R1'):
    stock = _financial_stock()
    stock['ticker'] = ticker
    packet = _packet(stock)
    view = _native(packet)
    owned = build_owned_evidence_packet(view.evidence, stock=stock)
    paired = dict(ticker=ticker, packet=packet,
                  evidence_packet=view.evidence.model_dump(mode='json'),
                  ownership=owned.model_dump(mode='json'))
    return stock, view, owned, paired


def test_completed_close_v2_unavailable_is_nonnumeric_limit_at_native_boundary():
    stock = _financial_stock()
    stock['current_price_context'] = dict(contract='current-price-context-v2',
        availability='UNAVAILABLE', current_price=987.654321, as_of_date='2026-06-30')
    packet = _packet(stock)
    view = _native(packet)
    owned = build_owned_evidence_packet(view.evidence, stock=stock)
    ref = next(row for row in owned.source_packet.evidence
               if row.ref_id == 'quality:current_price_context')
    projection = fundamental_ref_projection(ref)
    assert json.loads(projection.statement) == {
        'contract': 'price-quality-limit-v1', 'availability': 'unavailable',
        'use': 'EPISTEMIC_LIMIT_NOT_DIRECTIONAL_EVIDENCE'}
    assert projection.value is None and projection.as_of is None
    assert not projection.metric_refs and not projection.numeric_prose_eligible
    assert '987.654321' not in projection.model_dump_json()


@pytest.mark.parametrize(('contract', 'availability'), (
    (None, 'UNAVAILABLE'), ('current-price-context-v1', 'UNAVAILABLE'),
    ('unissued-version', 'UNAVAILABLE'), ('current-price-context-v2', 'READY'),
    ('current-price-context-v2', 'PRICE_ONLY'), ('current-price-context-v2', 'Available'),
))
def test_price_enum_conversion_does_not_expand_readiness_or_unknown_contracts(contract, availability):
    with pytest.raises(ValueError, match='fundamental_price_availability_invalid'):
        price_availability(availability, contract=contract)


@pytest.mark.parametrize('consumer', ('core_refs', 'timing_refs', 'domain_by_ref', 'technical_inventory'))
@pytest.mark.parametrize('mutation', ('domain', 'packet', 'missing_seal'))
def test_direct_consumer_rejects_unverified_owned_projection(consumer, mutation):
    _, _, owned, _ = _fixture()
    if mutation == 'domain':
        forged = owned.model_copy(update={'evidence': tuple(
            row.model_copy(update={'domain': EvidenceDomain.BUSINESS_CURRENT})
            for row in owned.evidence)})
    elif mutation == 'packet':
        forged = owned.model_copy(update={'source_packet': owned.source_packet.model_copy(
            update={'packet_id': 'different-invocation'})})
    else:
        forged = owned.model_copy(update={'backend_seal': None})
    with pytest.raises(ValueError, match='legacy_context_backend_seal'):
        technical_feature_inventory(forged) if consumer == 'technical_inventory' else getattr(forged, consumer)


@pytest.mark.parametrize('ticker', ('UNSEEN_US_R22R1', 'UNSEEN_KR_R22R1', 'UNSEEN_ADS_R22R1'))
def test_verified_same_parent_roundtrip_and_repeat_lookup(ticker):
    _, _, owned, _ = _fixture(ticker)
    for restored in (owned.model_copy(), owned.model_copy(deep=True),
                     OwnedEvidencePacket.model_validate_json(owned.model_dump_json())):
        assert restored.core_refs == owned.core_refs
        assert restored.timing_refs == owned.timing_refs
        assert restored.domain_by_ref == owned.domain_by_ref
        assert restored.core_refs == owned.core_refs


def test_explicit_empty_request_membership_does_not_inherit_owner_store():
    _, _, owned, _ = _fixture()
    ref = next(iter(owned.core_refs))
    def replace(value):
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        if isinstance(value, (tuple, list)):
            return [replace(item) for item in value]
        if isinstance(value, str) and value.startswith('canonical:fundamental:TEST:'):
            return ref
        return value
    raw = replace(_core().model_dump(mode='json'))
    raw['ticker'] = owned.source_packet.ticker
    candidate = DirectionalCoreCandidate.model_validate(raw)
    assert validate_directional_core_ownership(owned, candidate).valid
    assert validate_directional_core_ownership(owned, candidate, allowed_core_ref_ids=(ref,)).valid
    for supplied in ((), ('not-the-claimed-ref',)):
        result = validate_directional_core_ownership(owned, candidate, allowed_core_ref_ids=supplied)
        assert not result.valid
        assert 'directional_core_ref_not_supplied_to_stage' in result.errors


@pytest.mark.parametrize('consumer', (build_business_delta_evidence_view,
                                    build_market_expectation_evidence_view, _owned_context))
def test_raw_consumer_verifies_before_catalog_access(consumer):
    _, _, owned, _ = _fixture()
    core, timing = stage_alias_catalogs(owned)
    assert consumer(owned, core) is not None
    forged = owned.model_copy(update={'backend_seal': None})
    for catalog in (core, timing):
        with pytest.raises(ValueError, match='legacy_context_backend_seal_required'):
            consumer(forged, catalog)


@pytest.mark.parametrize('consumer', ('pair', 'source', 'monitor', 'preflight', 'time'))
def test_canonical_consumer_rejects_valid_seal_with_substituted_packet(consumer):
    _, _, _, paired = _fixture()
    paired['evidence_packet']['evidence'][0]['statement'] = 'Unadmitted source assertion 987.654321'
    with pytest.raises(ValueError, match='owned_evidence_consumer_packet_mismatch'):
        if consumer == 'pair':
            verified_owned_packet_view(paired)
        elif consumer == 'source':
            fresh_authority_inputs(paired, {})
        elif consumer == 'monitor':
            subject_inputs(paired, {}, {}, generation='not-issued')
        elif consumer == 'preflight':
            preflight_subject(paired, {}, {}, generation='not-issued', cutoff=None)
        else:
            reproject_time(paired)


def test_time_noop_retains_sanitized_projection_and_issued_seal():
    _, _, owned, paired = _fixture()
    projected, _, changes = reproject_time(paired)
    assert not changes
    assert projected == paired
    assert verified_owned_packet_view(projected) == owned


def test_time_change_requires_derivative_authority_not_caller_rehash():
    _, _, _, paired = _fixture()
    paired['packet']['stocks'][0]['fact_catalog'][0]['as_of_date'] = '2026-07-01'
    with pytest.raises(ValueError, match='owned_evidence_time_derivative_authority_required'):
        reproject_time(paired)


def test_source_time_only_change_requires_derivative_authority():
    _, _, _, paired = _fixture()
    as_of = [row['as_of'] for row in paired['evidence_packet']['evidence']]
    paired['packet']['generated_at'] = '2026-07-01T00:00:00+00:00'
    with pytest.raises(ValueError, match='owned_evidence_time_derivative_authority_required'):
        reproject_time(paired)
    assert [row['as_of'] for row in paired['evidence_packet']['evidence']] == as_of


@pytest.mark.parametrize('stage', ('core', 'timing'))
def test_owned_context_accepts_unchanged_exact_stage_catalog(stage):
    _, _, owned, _ = _fixture()
    core, timing = stage_alias_catalogs(owned)
    result = _owned_context(owned, core if stage == 'core' else timing)
    assert result['ticker'] == owned.source_packet.ticker


@pytest.mark.parametrize('field', ('ticker', 'market', 'generation', 'evidence_fingerprint',
                                 'alias_map_sha256', 'label', 'statement', 'as_of', 'metric_refs'))
def test_owned_context_rejects_detached_catalog_substitution(field):
    _, _, owned, _ = _fixture()
    catalog, _ = stage_alias_catalogs(owned)
    if field in {'label', 'statement', 'as_of', 'metric_refs'}:
        value = ('unadmitted_metric',) if field == 'metric_refs' else 'Unadmitted 987.654321'
        entries = (catalog.entries[0].model_copy(update={field: value}), *catalog.entries[1:])
        forged = catalog.model_copy(update={'entries': entries})
    else:
        forged = catalog.model_copy(update={field: 'unadmitted-identity'})
    with pytest.raises(ValueError, match='owned_context_stage_catalog_mismatch'):
        _owned_context(owned, forged)


def test_rehashed_catalog_cannot_grant_text_authority():
    _, _, owned, _ = _fixture()
    core, _ = stage_alias_catalogs(owned)
    refs = set(core.by_ref)
    rows = tuple(row.ref.model_copy(update={'statement': 'Unadmitted economic growth 987.654321'})
                 for row in owned.evidence if row.ref.ref_id in refs)
    forged = build_evidence_alias_catalog(owned.source_packet.model_copy(update={'evidence': rows}))
    with pytest.raises(ValueError, match='owned_context_stage_catalog_mismatch'):
        _owned_context(owned, forged)


def test_simulated_inherited_owner_pid_rejects_issue_and_lookup(monkeypatch):
    _, view, _, _ = _fixture()
    monkeypatch.setattr(authority, '_OWNER_PID', -1)
    for operation in (lambda: authority.verify_legacy_context(view.context),
                      lambda: authority._seal_built_context(view.context)):
        with pytest.raises(ValueError, match='legacy_context_owner_process_mismatch'):
            operation()


def test_new_interpreter_rejects_parent_receipt(tmp_path):
    _, view, _, _ = _fixture()
    payload = tmp_path/'context.json'
    payload.write_text(view.context.model_dump_json())
    code = '''
import json, os, sys
from pathlib import Path
from app.services.accepted_decision_v2_runtime_service import AcceptedV2ProductionContext
from app.services.legacy_context_authority import verify_legacy_context
context = AcceptedV2ProductionContext.model_validate_json(Path(sys.argv[1]).read_text())
try:
    verify_legacy_context(context)
except ValueError as exc:
    print(json.dumps({'pid': os.getpid(), 'error': str(exc)}))
else:
    raise SystemExit('UNEXPECTED_CROSS_PROCESS_ACCEPT')
'''
    child = subprocess.run([sys.executable, '-B', '-c', code, str(payload)],
                           cwd=Path(__file__).resolve().parents[1],
                           text=True, capture_output=True, timeout=30, check=False)
    assert child.returncode == 0, child.stderr
    result = json.loads(child.stdout)
    assert result['error'] == 'legacy_context_backend_seal_mismatch'
    authority.verify_legacy_context(view.context)
    (tmp_path/'r22r1-new-process-proof.json').write_text(json.dumps(result)+'\n')


def test_consumer_market_cannot_differ_from_sealed_packet():
    _, _, _, paired = _fixture()
    paired['market'] = 'kr'
    with pytest.raises(ValueError, match='owned_evidence_consumer_packet_mismatch'):
        verified_owned_packet_view(paired)


def test_schema_uses_sanitized_logical_and_date_projection():
    stock = _financial_stock()
    stock['current_price_context'] = {'availability': 'unavailable', 'current_price': 987.654321}
    packet = _packet(stock)
    evidence = build_decision_evidence_packet(packet=packet, stock=stock)
    poisoned = []
    for row in evidence.evidence:
        if row.financial_context is not None or row.ref_id == 'quality:current_price_context':
            updates = {'logical_condition': source_logical_condition(subject=stock['ticker'],
                generation_id='unadmitted-logic', evidence_ref=row.ref_id,
                statement='Unadmitted extra economic condition', severity=LogicalSeverity.STRENGTHENING)}
            if row.ref_id == 'quality:current_price_context':
                updates['as_of'] = '2099-01-01'
            row = row.model_copy(update=updates)
        poisoned.append(row)
    view = _native(packet, evidence=evidence.model_copy(update={'evidence': tuple(poisoned)}))
    assert 'Unadmitted extra economic condition' not in view.prompt
    for catalog in (runtime.accepted_v2_fundamental_core_ref_catalog_manifest(view.context),
                    runtime.accepted_v2_stage2_ref_catalog_manifest(view.context)):
        assert catalog['allowed_source_condition_refs'] == []
        assert catalog['allowed_leaf_refs'] == []
        assert '2099-01-01' not in json.dumps(catalog)
    schema = runtime.accepted_v2_fundamental_core_output_schema(view.context)
    assert schema['$defs']['EvidenceClaim']['properties']['logical_condition'] == {'type': 'null'}
    assert schema['$defs']['ClaimLogicalCondition']['properties']['source_condition_ref']['enum'] == []
    assert schema['$defs']['ClaimLogicalLeaf']['properties']['leaf_ref']['enum'] == []


@pytest.mark.parametrize('source_refs,leaf_refs', ((('source',), ()), ((), ('leaf',))))
def test_half_empty_logical_catalog_still_rejected(source_refs, leaf_refs):
    with pytest.raises(ValueError, match='logical_ref_catalog_incomplete'):
        runtime._exact_ref_output_schema(runtime.AcceptedV2FundamentalCoreBatch.model_json_schema(),
            evidence_ref_fields=(('EvidenceClaim', 'evidence_refs'),), refs=('ref',),
            source_condition_refs=source_refs, leaf_refs=leaf_refs, error_prefix='probe')


def test_empty_catalog_does_not_hide_malformed_definition():
    schema = runtime.AcceptedV2FundamentalCoreBatch.model_json_schema()
    schema['$defs']['ClaimLogicalLeaf']['properties']['leaf_ref']['type'] = 'number'
    before = deepcopy(schema)
    with pytest.raises(ValueError, match='logical_ref_schema_not_string'):
        runtime._exact_ref_output_schema(schema, evidence_ref_fields=(('EvidenceClaim', 'evidence_refs'),),
            refs=('ref',), source_condition_refs=(), leaf_refs=(), error_prefix='probe')
    assert schema == before
