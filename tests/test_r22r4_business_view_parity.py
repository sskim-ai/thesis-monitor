import json

import pytest
from pydantic import ValidationError

from app.services import reviewed_fixture_authority as owner
from app.services.business_delta_evidence_service import (
    BusinessDeltaCapability,
    BusinessDeltaEvidenceView,
    attach_business_delta_evidence_view,
    build_business_delta_evidence_view,
)
from app.services.fixture_context_authority import reject_test_only_production
from test_reviewed_fixture_authority_r22r3 import fixture, projection


@pytest.mark.parametrize('kind', ('financial', 'delta', 'canary'))
def test_legacy_public_view_retains_owned_envelope_and_revocation(kind):
    owned = fixture(kind)
    catalog, context = projection(owned)
    view = build_business_delta_evidence_view(owned, catalog, context=context)
    public = view.model_context()
    assert public['contract'] == 'business-delta-evidence-view-v1'
    assert set(public) == {
        'contract', 'capability', 'allowed_business_thesis_changes',
        'baseline_context_refs', 'eligible_change_refs', 'eligible_change_direction_hints',
        'excluded_change_refs', 'excluded_change_ref_count',
    }
    assert 'test_only_provenance' not in json.loads(json.dumps(public))
    with pytest.raises(ValueError, match='production_test_only_fixture_forbidden'):
        reject_test_only_production(public)
    envelope = attach_business_delta_evidence_view(context, view)
    with pytest.raises(ValueError, match='production_test_only_fixture_forbidden'):
        reject_test_only_production(json.loads(json.dumps(envelope)))
    serialized = view.model_dump(mode='json')
    serialized.pop('test_only_provenance')
    serialized['contract'] = 'business-delta-evidence-capability-v1'
    forged = BusinessDeltaEvidenceView.model_validate(serialized)
    with pytest.raises(ValueError, match='reviewed_fixture_view_parent_required'):
        forged.model_context()
    owner.revoke_reviewed_fixture(owned)
    with pytest.raises(ValueError, match='reviewed_fixture_unissued_revoked_or_changed'):
        view.model_context()


@pytest.mark.parametrize('key', ('ticker', 'capability', 'eligible_change_refs'))
def test_legacy_public_projection_still_requires_exact_parent_semantics(key):
    owned = fixture('financial')
    catalog, context = projection(owned)
    view = build_business_delta_evidence_view(owned, catalog, context=context)
    changed_capability = BusinessDeltaCapability.AI_JUDGMENT if view.capability == BusinessDeltaCapability.UNCHANGED_ONLY else BusinessDeltaCapability.UNCHANGED_ONLY
    replacement = {'ticker': 'WRONG', 'capability': changed_capability, 'eligible_change_refs': ('E999',)}[key]
    with pytest.raises(ValueError, match='reviewed_fixture_view_projection_mismatch'):
        view.model_copy(update={key: replacement}).model_context()


@pytest.mark.parametrize('kind', ('financial', 'delta', 'canary'))
def test_anonymous_public_json_is_not_a_typed_fact_or_issuance(kind):
    owned = fixture(kind)
    catalog, context = projection(owned)
    view = build_business_delta_evidence_view(owned, catalog, context=context)
    public = json.loads(json.dumps(view.model_context()))
    before = dict(owner._ISSUED)
    with pytest.raises(ValidationError):
        BusinessDeltaEvidenceView.model_validate(public)
    public['eligible_change_refs'] = ['E999']
    public['capability'] = 'CALLER_APPROVED'
    rebuilt = build_business_delta_evidence_view(owned, catalog, context={
        **context, 'business_delta_evidence_view': public,
    })
    assert rebuilt == view
    assert owner._ISSUED == before
