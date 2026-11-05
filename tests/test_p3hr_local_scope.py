"""Local-only intake approval does not assert remote exclusivity."""
from datetime import datetime, timedelta, timezone

import pytest

from tests.test_p3g_pending_worker import prepared
from tests.test_p3f_source_intake import pending
from app.services import pending_source_intake as intake
from app.services import prospective_class_c_owner as approval_owner


def approval():
    now = datetime.now(timezone.utc)
    return approval_owner.record_backend_approval(approval_owner.ApprovalDecision(
        event_id='TEST_LOCAL_SCOPE', user_message_sha256='a'*64, approved=True,
        effective_at=now, expires_at=now+timedelta(minutes=10), subjects=('FUTURE',)))


def test_exact_original_session_required():
    with pytest.raises(ValueError, match='original_local_session'):
        intake.record_backend_local_scope(approval=approval(), session=object(),
            generation_id='TEST', source_generation_id='TEST', enabled=True)


def test_original_local_session_and_one_use(prepared):
    args, _, _ = prepared
    approved = approval()
    options = dict(approval=approved, session=args['session'], generation_id='LOCAL',
        source_generation_id='LOCAL', enabled=True)
    scope = intake.record_backend_local_scope(**options)
    state, _ = intake._scope(scope)
    assert state['remote_account_exclusivity'] == 'NOT_OBSERVABLE'
    assert state['policy'] == 'PENDING_READ_ONLY_LOCAL_SERIALIZATION_V1'
    with pytest.raises(ValueError, match='original_local_session'):
        intake.record_backend_local_scope(**options)
    approval_owner.revoke_approval(approved)
    with pytest.raises(ValueError):
        intake._scope(scope)


def test_unregistered_subject_cannot_enter_subset(prepared):
    from app.services import pending_source_parent as parent
    args, _, _ = prepared
    config = args['config']
    unknown = config.subjects[0].model_copy(update={'ticker': 'UNREGISTERED'})
    changed = config.model_copy(update={'subjects': (unknown,)})
    with pytest.raises(ValueError, match='exact_subjects'):
        parent.issue_parent(**dict(args, config=changed))
