import pytest

from app.services.owned_evidence_derivative import restrict_owned_evidence, revoke_owned_derivative
from tests.test_legacy_consumer_boundaries_r22r1 import _fixture
from tests.test_core_input_source_isolation_r21 import _isolated_data as _isolated_data


@pytest.mark.parametrize('ticker', ('UNSEEN_US_REPLAY', 'UNSEEN_KR_REPLAY', 'UNSEEN_ADS_REPLAY'))
def test_live_exact_derivation_is_idempotent_in_producer_order(ticker):
    _, _, parent, _ = _fixture(ticker)
    refs = tuple(sorted(parent.core_refs))
    first = restrict_owned_evidence(parent, retained_refs=refs, purpose='DENIED_USE_FILTER')
    second = restrict_owned_evidence(parent.model_copy(deep=True), retained_refs=refs[::-1], purpose='DENIED_USE_FILTER')
    assert first.model_dump_json() == second.model_dump_json()
    assert first.core_refs == second.core_refs
    other = restrict_owned_evidence(parent, retained_refs=refs, purpose='REQUEST_REF_RESTRICTION')
    assert other.backend_seal.receipt_id != first.backend_seal.receipt_id
    assert other.backend_seal.payload_sha256 == first.backend_seal.payload_sha256


def test_revoke_child_does_not_resurrect_old_receipt():
    _, _, parent, _ = _fixture()
    first = restrict_owned_evidence(parent, retained_refs=(), purpose='DENIED_USE_FILTER')
    revoke_owned_derivative(first)
    second = restrict_owned_evidence(parent, retained_refs=(), purpose='DENIED_USE_FILTER')
    assert second.backend_seal.receipt_id != first.backend_seal.receipt_id
    with pytest.raises(ValueError, match='unissued'):
        _ = first.core_refs
    assert not second.core_refs


def test_parent_receipt_identity_and_revocation_bind_repeated_derivation():
    _, _, root, _ = _fixture()
    parent = restrict_owned_evidence(root, retained_refs=tuple(root.core_refs), purpose='DENIED_USE_FILTER')
    old = restrict_owned_evidence(parent, retained_refs=(), purpose='DENIED_USE_FILTER')
    revoke_owned_derivative(parent)
    with pytest.raises(ValueError, match='unissued'):
        restrict_owned_evidence(parent, retained_refs=(), purpose='DENIED_USE_FILTER')
    new_parent = restrict_owned_evidence(root, retained_refs=tuple(root.core_refs), purpose='DENIED_USE_FILTER')
    new = restrict_owned_evidence(new_parent, retained_refs=(), purpose='DENIED_USE_FILTER')
    assert old.backend_seal.receipt_id != new.backend_seal.receipt_id
    assert not new.core_refs
    with pytest.raises(ValueError, match='unissued'):
        _ = old.core_refs


def test_no_reuse_before_original_membership_and_payload_checks():
    _, _, parent, _ = _fixture()
    first = restrict_owned_evidence(parent, retained_refs=(), purpose='DENIED_USE_FILTER')
    with pytest.raises(ValueError, match='duplicate_ref'):
        restrict_owned_evidence(parent, retained_refs=('bad', 'bad'), purpose='DENIED_USE_FILTER')
    with pytest.raises(ValueError, match='membership_expansion'):
        restrict_owned_evidence(parent, retained_refs=('bad',), purpose='DENIED_USE_FILTER')
    changed = parent.model_copy(update={'sector_framework':'CALLER_REPLACED'})
    with pytest.raises(ValueError, match='seal_mismatch'):
        restrict_owned_evidence(changed, retained_refs=(), purpose='DENIED_USE_FILTER')
    assert not first.core_refs
