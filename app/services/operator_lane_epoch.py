"""Explicit cold restart of an ambiguous legacy STOP under the original lock.

This is an operator control, not automatic semantic recovery. A crash between
state and activation replacement leaves original readers denied by generation
mismatch. The same operation can complete only from its sealed exact intent.
"""
import hashlib,json,os,re,stat,time
from pathlib import Path
from app.services import kiwoom_global_lane as protocol

CONTRACT='operator-acknowledged-legacy-cold-restart-v1'

def _sha(raw):return hashlib.sha256(raw).hexdigest()

def _seal(path,raw):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        if os.write(fd,raw)!=len(raw):raise ValueError('epoch_archive_short_write')
        os.fsync(fd)
    finally:os.close(fd)
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)

def _raw(path):
    protocol._private(path)
    return path.read_bytes()

def acknowledge_cold_restart(root, *, operation_id, expected_state_sha256,
        expected_activation_sha256, expected_lock_identity, operator_message_sha256,
        account_exclusive_confirmed, quiet_pids, explicit_approval=False, _crash_at=None):
    """Do not call until current host/process/ledger admission has been reviewed.

    No credential, HTTP or service operation. Inputs are frozen by the trusted
    local operator entrypoint, not accepted from a source or model payload.
    """
    if (explicit_approval is not True or account_exclusive_confirmed is not True
            or not re.fullmatch(r'[a-zA-Z0-9_-]{8,80}',operation_id)
            or any(not re.fullmatch(r'[0-9a-f]{64}',s) for s in
                   (expected_state_sha256,expected_activation_sha256,operator_message_sha256))):
        raise ValueError('epoch_explicit_operator_admission_required')
    root=Path(root).absolute();protocol._private(root,True)
    # Constructor checks the real boot and implementation. During an interrupted
    # transition activation remains the prior valid activation until last commit.
    lane=protocol.GlobalKiwoomLane(root)
    if tuple(expected_lock_identity)!=lane.lock_identity:raise ValueError('epoch_lock_changed')
    fd=lane._open()
    try:
        if not lane._try_lock(fd):raise ValueError('epoch_live_lock_busy')
        archive=root/'operator-epochs'
        if not archive.exists():archive.mkdir(mode=0o700)
        protocol._private(archive,True)
        journal=archive/operation_id
        state_raw=_raw(root/'state.json');activation_raw=_raw(root/'activation.json')
        if journal.exists():
            protocol._private(journal,True)
            intent=json.loads(_raw(journal/'intent.json'))
            if (intent['operator_message_sha256']!=operator_message_sha256
                    or intent['old_state_sha256']!=expected_state_sha256
                    or intent['old_activation_sha256']!=expected_activation_sha256
                    or tuple(intent['lock_identity'])!=lane.lock_identity):
                raise ValueError('epoch_intent_identity_changed')
            old_state=_raw(journal/'state.json');old_activation=_raw(journal/'activation.json')
            if _sha(old_state)!=expected_state_sha256 or _sha(old_activation)!=expected_activation_sha256:
                raise ValueError('epoch_archive_hash_mismatch')
            new_state=json.dumps(intent['new_state'],sort_keys=True,allow_nan=False).encode()
            new_activation=json.dumps(intent['new_activation'],sort_keys=True,allow_nan=False).encode()
            if (journal/'complete.json').exists():
                if state_raw!=new_state or activation_raw!=new_activation:
                    raise ValueError('epoch_already_used_state_moved')
                return json.loads(_raw(journal/'complete.json'))
            if state_raw not in (old_state,new_state) or activation_raw not in (old_activation,new_activation):
                raise ValueError('epoch_interrupted_state_unknown')
        else:
            if _sha(state_raw)!=expected_state_sha256 or _sha(activation_raw)!=expected_activation_sha256:
                raise ValueError('epoch_stop_hash_mismatch')
            state=protocol._read(root/'state.json')
            if (not state['halted'] or state['in_flight'] or state['boot_identity']!=protocol.boot_identity()
                    or state['generation']!=lane.activation['generation'] or state['protocol']!=protocol.PROTOCOL):
                raise ValueError('epoch_not_quiet_halted_generation')
            # The last owner PID is always included, even if the caller omitted it.
            for pid in set(quiet_pids)|{state['pid']}:
                if type(pid) is not int or pid<=0:raise ValueError('epoch_pid_invalid')
                try:os.kill(pid,0)
                except ProcessLookupError:pass
                else:raise ValueError('epoch_prior_process_live_or_unknown')
            journal.mkdir(mode=0o700)
            _seal(journal/'state.json',state_raw);_seal(journal/'activation.json',activation_raw)
            next_activation=dict(lane.activation,generation='operator-'+operation_id)
            next_state=dict(state,generation=next_activation['generation'],halted=False,in_flight=False,pid=os.getpid())
            # Keep last_end and sequence; neither pacing nor usage history resets.
            intent=dict(contract=CONTRACT,reason='OPERATOR_ACKNOWLEDGED_LEGACY_CAUSE_AMBIGUOUS',
                old_state_sha256=expected_state_sha256,old_activation_sha256=expected_activation_sha256,
                operator_message_sha256=operator_message_sha256,lock_identity=list(lane.lock_identity),
                old_generation=state['generation'],old_sequence=state['sequence'],new_state=next_state,
                new_activation=next_activation,created_at=time.time())
            _seal(journal/'intent.json',json.dumps(intent,sort_keys=True).encode())
        if intent['new_state']['boot_identity']!=protocol.boot_identity():
            raise ValueError('epoch_boot_changed')
        original=json.loads(_raw(journal/'state.json'))
        for pid in set(quiet_pids)|{original['pid']}:
            try:os.kill(pid,0)
            except ProcessLookupError:pass
            else:raise ValueError('epoch_prior_process_live_or_unknown')
        # Stale pre-restart participants retain the old activation and are denied.
        # All mutation is through the original durable atomic writer and OS lock.
        if _crash_at=='before_state':raise RuntimeError('epoch_injected_crash_before_state')
        protocol._atomic(root/'state.json',intent['new_state'])
        if _crash_at=='after_state':raise RuntimeError('epoch_injected_crash_after_state')
        protocol._atomic(root/'activation.json',intent['new_activation'])
        if _crash_at=='after_activation':raise RuntimeError('epoch_injected_crash_after_activation')
        receipt=dict(contract=CONTRACT,status='NEW_EPOCH_COMMITTED',reason=intent['reason'],
            old_generation=intent['old_generation'],new_generation=intent['new_activation']['generation'],
            old_STOP_preserved=True,old_sequence=intent['old_sequence'],new_sequence=intent['new_state']['sequence'],
            old_state_sha256=expected_state_sha256,lock_identity=list(lane.lock_identity),
            transport_policy_unchanged=True,semantic_only_proven=False,HTTP=0)
        _seal(journal/'complete.json',json.dumps(receipt,sort_keys=True).encode())
        return receipt
    finally:os.close(fd)
