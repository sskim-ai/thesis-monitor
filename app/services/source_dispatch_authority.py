"""Exact capability-type dispatch. ACTIVE Owner behavior stays unchanged."""
from app.services import current_scoped_source_owner as active
from app.services import pending_source_parent as pending

def _owner(parent):
    return pending if type(parent) is pending.PendingSourceParent else active
def resolve_parent(parent,*,plan=None):return _owner(parent).resolve_parent(parent,plan=plan)
def authorize_descriptor(parent,descriptor,*,plan):return _owner(parent).authorize_descriptor(parent,descriptor,plan=plan)
def revoke_parent(parent):return _owner(parent).revoke_parent(parent)
def require_worker_dispatch(parent):
    if type(parent) is pending.PendingSourceParent:
        s=pending.state(parent)
        pending.require_worker(parent,s['worker_pid'],physical=True)
