"""Explicit parent-owned non-HTTP admission. Does not activate live services."""
import os
from app.services import kiwoom_global_lane as lane_module
from app.services.runtime_maintenance import RequestDrain, MaintenanceDenied, loaded_identity


class ParticipatingSession:
    def __init__(self, *, modules, caller_kind):
        if caller_kind not in ('HTTP','CLI','SCHEDULED_JOB'):
            raise ValueError('unsupported_participant_kind')
        self._pid=os.getpid();self._modules=tuple(modules);self.kind=caller_kind
        self._lane=lane_module.configured_lane()
        if self._lane is None:raise MaintenanceDenied('participant_requires_opted_in_lane')
        self._boot=lane_module.boot_identity()
        self._identity=[loaded_identity(m) for m in self._modules]
        if not self._identity:raise MaintenanceDenied('participant_loaded_identity_required')
        self._drain=RequestDrain();self._restore_ticket=None
        self._check()

    def _check(self):
        if os.getpid()!=self._pid or lane_module.boot_identity()!=self._boot:
            raise MaintenanceDenied('participant_process_or_boot_changed')
        if lane_module.configured_lane() is not self._lane:
            raise MaintenanceDenied('participant_lane_changed')
        current=[loaded_identity(m) for m in self._modules]
        # loaded_identity checks each code object against freshly compiled source.
        # marshal's reference/intern encoding is not a stable execution identity.
        keys=('path','source_sha256','definitions','excluded_generated')
        if [tuple(i[k] for k in keys) for i in self._identity]!=[tuple(i[k] for k in keys) for i in current]:
            raise MaintenanceDenied('participant_loaded_identity_changed')
        if lane_module._read(self._lane.root/'activation.json')!=self._lane.activation:
            raise MaintenanceDenied('participant_activation_changed')
        fd=self._lane._open();os.close(fd)

    def operation(self):
        self._check()
        return self._drain.operation()

    def close_admission(self,timeout=5):
        self._check();snapshot=self._drain.drain(timeout)
        self._restore_ticket=object()
        return self._restore_ticket,dict(snapshot,scope='THIS_ENROLLED_PROCESS_ALL_WRAPPED_OPERATIONS',caller_kind=self.kind)

    def restore(self,ticket):
        self._check()
        if ticket is not self._restore_ticket or ticket is None or self._drain.snapshot()['active']:
            raise MaintenanceDenied('participant_restore_capability_denied')
        # A fresh local gate does not reset the persistent lane denial/crash state.
        self._drain=RequestDrain();self._restore_ticket=None

    def attestation(self):
        self._check()
        return dict(pid=self._pid,boot_identity=self._boot,loaded=self._identity,
            lock_identity=list(self._lane.lock_identity),activation=dict(self._lane.activation),
            caller_kind=self.kind,operations=dict(self._drain.snapshot(),scope='THIS_ENROLLED_PROCESS_ALL_WRAPPED_OPERATIONS'),
            scope='ENROLLED_PROCESS_ONLY_NOT_GLOBAL_ACCOUNT_ATTESTATION')
