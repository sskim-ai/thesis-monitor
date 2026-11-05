"""Read-only recovery review. Legacy boolean STOP cannot prove a unique cause.

This entrypoint intentionally has no state-reset executor. A later explicit
operation must supply authoritative cause attribution, not a caller JSON label.
"""
import os
from app.services import kiwoom_global_lane as lane_module
from app.services.unified_snapshot_contract import digest


def review_recovery(lane, *, expected_state_sha256, expected_lock_identity, worker_pids=()):
    if type(lane) is not lane_module.GlobalKiwoomLane:
        raise ValueError('recovery_original_lane_required')
    fd=lane._open()
    try:
        if not lane._try_lock(fd):
            raise ValueError('recovery_actual_lock_busy')
        if tuple(expected_lock_identity) != tuple(lane.lock_identity):
            raise ValueError('recovery_lock_identity_changed')
        state=lane_module._read(lane.root/'state.json')
        if digest(state) != expected_state_sha256:
            raise ValueError('recovery_stop_receipt_changed')
        if state['boot_identity'] != lane_module.boot_identity() or not state['halted'] or state['in_flight']:
            raise ValueError('recovery_boot_or_inflight_state_denied')
        for pid in worker_pids:
            try: os.kill(pid,0)
            except ProcessLookupError: pass
            else: raise ValueError('recovery_worker_not_proven_exited')
        # The inherited durable schema has only halted/in_flight/sequence/pid.
        # Matching a bad row and sequence does not cryptographically exclude an
        # additional transport, pacing or custody fault at that same boundary.
        return dict(contract='semantic-stop-recovery-review-v1',status='BLOCKED_LEGACY_STOP_CAUSE_NOT_ATTESTED',
            state_sha256=digest(state),sequence=state['sequence'],lock_identity=list(lane.lock_identity),
            explicit_execution_approval_required=True,recovery_executable=False,STOP_reset=False,
            required='Original authoritative unique stop-cause receipt and separately approved recovery operation')
    finally: os.close(fd)
