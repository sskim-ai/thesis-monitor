"""New version boundary tests only; synthetic judgments are not model receipts."""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import pytest
from app.services import vnext_unified_judgment as engine
from app.services.versioned_source_replay import VersionedSourceReplay, CONTRACT
from app.services.vnext_daily_research import UseRegistry
from test_vnext_ai_owned_judgment import setup, check


def bound():
    economic, packet, value, registry = setup()
    schema = engine.schema(security_id=packet['base']['public_security']['canonical_security_id'],
                           contract=packet['contract'])
    def original(method):
        assert method == 'rebuild'
        return dict(contract=CONTRACT, packet=deepcopy(packet), economic=deepcopy(economic),
                    schema=deepcopy(schema), producer_identity={'synthetic': True},
                    dated_only=True, current_source=False, original_owner_replayed=True)
    owner = VersionedSourceReplay(producer=original, verify_environment=lambda: True,
        packet=packet, consumer_schema=schema, consumer_identity={'synthetic': True}, registry=registry, enabled=True)
    return economic, packet, value, registry, owner


def test_actual_validation_hook_matches_original_default():
    p, b, v, r, owner = bound()
    expected = check(p, b, v, r)
    actual = engine.validate_and_render(v, b, registry=r, economic_loader=owner.economic_loader,
                                       versioned_source_owner=owner)
    assert actual == expected


def test_json_is_not_a_versioned_source_owner():
    p, b, v, r, owner = bound()
    with pytest.raises(ValueError, match='versioned_original_source_capability_required'):
        engine.validate_and_render(v, b, registry=r, economic_loader=lambda: p,
                                   versioned_source_owner={'accepted': True})


def test_original_exact_economic_input_remains_required():
    p, b, v, r, owner = bound()
    altered = deepcopy(p);altered['unapproved_financial_value'] = 1
    with pytest.raises(ValueError, match='versioned_exact_owner_input_required'):
        engine.validate_and_render(v, b, registry=r, economic_loader=lambda: altered,
                                   versioned_source_owner=owner)


def test_closed_owner_cannot_validate_a_stage():
    p, b, v, r, owner = bound();owner.revoke()
    with pytest.raises(ValueError, match='changed_or_closed'):
        engine.validate_and_render(v, b, registry=r, economic_loader=lambda: p,
                                   versioned_source_owner=owner)


def test_one_byte_changed_historical_stage_rejected_before_producer(tmp_path):
    original = Path(os.environ['C21Q_ORIGINAL_STAGE_PATH']).read_bytes()
    pin = hashlib.sha256(original).hexdigest()
    changed = tmp_path/'old_stage.py';changed.write_bytes(original+b'\n')
    def no_rpc(method):
        pytest.fail('Changed source must fail before producer RPC')
    with pytest.raises(ValueError, match='changed_or_closed'):
        VersionedSourceReplay(producer=no_rpc,
            verify_environment=lambda: hashlib.sha256(changed.read_bytes()).hexdigest() == pin,
            packet={}, consumer_schema={}, consumer_identity={}, registry=UseRegistry(), enabled=True)


def test_versioned_owner_default_off():
    with pytest.raises(ValueError, match='default_off'):
        VersionedSourceReplay(producer=lambda method: {}, verify_environment=lambda: True,
                              packet={}, consumer_schema={}, consumer_identity={}, registry=UseRegistry())


def test_parent_registry_revocation_blocks_before_stage():
    p, b, v, r, owner = bound()
    r.revoke(b['base']['public_security']['canonical_security_id'], p['base']['evidence'][0]['source_sha'])
    with pytest.raises(ValueError, match='versioned_source_use_revoked'):
        owner.source_loader()


def test_foreign_registry_cannot_replace_parent_registry():
    p, b, v, r, owner = bound()
    with pytest.raises(ValueError, match='versioned_exact_owner_input_required'):
        engine.validate_and_render(v, b, registry=UseRegistry(),
            economic_loader=owner.economic_loader, versioned_source_owner=owner)
