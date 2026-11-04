"""Original-purpose denials, not a new manual admission capability."""
import pytest
from pydantic import ValidationError

from app.services.accepted_decision_v2_runtime_service import build_accepted_v2_economic_core_invocation
from app.services.native_economic_core import InvocationSpec
from app.services.native_owner_session import BackendOwnerParent, ParentAdmissionManifest
from app.services.prospective_class_c_owner import SCOPE
from app.services.unified_snapshot_contract import digest
from tests.test_economic_claim_qualification import claim_fixture
from tests.test_native_owner_session import composition, session


def replacement_purpose(invocation, policy, purpose):
    current = invocation.request
    fields = {name: getattr(current.invocation, name) for name in InvocationSpec.model_fields}
    fields['execution_purpose'] = purpose
    spec = InvocationSpec(**fields)
    return build_accepted_v2_economic_core_invocation(
        context=current.reference_request.context,
        admission_registry=invocation._registry,
        invocation_spec=spec,
        economic_policy=policy,
        authority_native_v2=True,
    )


def test_manual_purpose_cannot_be_aliased_to_original_native_contract(record_property):
    _, policy, invocation, _ = claim_fixture()
    with pytest.raises(ValidationError) as error:
        replacement_purpose(invocation, policy, SCOPE)
    assert any(row['loc'] == ('execution_purpose',) and row['type'] == 'literal_error'
               for row in error.value.errors())
    record_property('ng17_manual_admission', dict(
        status='NG17_MANUAL_NATIVE_ADMISSION_PENDING',
        original_native_purpose_rejected=SCOPE,
        manual_capability_issued=False, real_source_qualification=False))


def test_genuine_accepted_core_purpose_does_not_widen_offline_parent():
    _, policy, invocation, _ = claim_fixture()
    accepted = replacement_purpose(invocation, policy, 'ACCEPTED_CORE_MODEL_REPROOF')
    parent, _, _ = composition(accepted, register=False)
    with pytest.raises(ValueError, match='PARENT_OFFLINE_SCOPE_ONLY'):
        parent.register(accepted)
    with pytest.raises(ValueError, match='UNISSUED_PARENT_INVOCATION'):
        parent.begin(accepted.request.invocation.invocation_id)
    assert not parent._attempts and not parent._invocations


@pytest.mark.parametrize('binding', ['empty', 'wrong_source_envelope'])
def test_empty_or_rehashed_manifest_cannot_register_or_begin(binding, tmp_path):
    _, _, invocation, _ = claim_fixture()
    original, scope, body = composition(invocation, register=False)
    fields = original._manifest.model_dump(mode='json')
    if binding == 'empty':
        fields['invocations'] = []
    else:
        fields['invocations'][0]['source_envelope_sha256'] = '0' * 64
    manifest = ParentAdmissionManifest(**fields)
    parent = BackendOwnerParent(authority_native_v2=True, **scope,
        admission_manifest=manifest,
        expected_manifest_sha256=digest(manifest.model_dump(mode='json')))
    stage = session(tmp_path / 'unissued', parent, scope, body)
    with pytest.raises(ValueError, match='PARENT_SNAPSHOT_ADMISSION_MEMBERSHIP_MISMATCH'):
        parent.register(invocation)
    with pytest.raises(ValueError, match='UNISSUED_PARENT_INVOCATION'):
        stage.native_context_prompt(invocation.request.invocation.invocation_id, {})
    assert not parent._attempts and not parent._invocations
    assert not stage.captured and not stage.root.exists()
