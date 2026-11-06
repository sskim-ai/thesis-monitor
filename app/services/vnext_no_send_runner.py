"""Explicit Unix shadow runner; no installed schedule, transport, or sender.

Only trusted Python backend capabilities enter the child. A public JSON job is
never imported as executable code or rehydrated as an Owner. The isolated shared
journal coordinates participating parents; it does not provide cross-host locks.
"""
from datetime import datetime, timezone
from copy import deepcopy
import fcntl
import json
import math
import os
import signal
import stat
import threading
import time
import uuid

from app.services.vnext_no_send_controller import NoSendController, calendar_gate, MODEL
from app.services.vnext_research_store import digest, encoded, plain
from app.services.vnext_public_capture import target_session
from app.services.vnext_execution_profile import ASTRA_XHIGH_V1, require_profile

CONTRACT = 'isolated-no-send-host-runner-v1'
MAX_SECONDS = 600
MAX_RESULT_BYTES = 4 * 1024**2


class CapturedSourceRecovery:
    """Explicit once-only repair of a known overlap-revision rejection.

    No capture capability is retained. A live corrected original Delta Owner,
    terminated original host, absence of model intents and new operator review
    are all required. The consumed daily cycle is never cleared or replaced.
    """
    def __init__(self, *, config, bridge_request, owner, approval):
        from app.services.vnext_incremental_ingestion import DailyDeltaOwner
        if type(owner) is not DailyDeltaOwner or not callable(approval):
            raise ValueError('captured_recovery_live_owner_required')
        if config.environment != 'test' or config.mode != 'write':
            raise ValueError('captured_recovery_isolated_only')
        self._store=config.validate()
        self._bridge=deepcopy(bridge_request)
        self.owner=owner
        self._batch=digest(owner.batch())
        self._approval=approval

    def authorize(self, controller, slot_request, original):
        if (controller.config.validate()!=self._store or not original or
                original.get('state')!='CALLBACK_FAILED' or original.get('exit')!=1 or
                original.get('failure',{}).get('error_code')!='same_session_revision_requires_reason' or
                original.get('response') is not None or not original.get('guardian_pid') or
                original.get('guardian_cleanup')!='OWNED_LIVE_SESSION_SIGKILL_THEN_REAP'):
            raise ValueError('captured_recovery_known_terminal_required')
        with controller.store.connect() as conn:
            records=dict(conn.execute('SELECT key,value FROM research_meta'))
        if any('daily-primary-' in key for key in records):
            raise ValueError('captured_recovery_no_model_intent_required')
        def job(suffix):
            raw=records.get('vnext-runtime-v1:job:'+original['attempt']+suffix)
            if raw is None:raise ValueError('captured_recovery_original_journal_missing')
            row=json.loads(raw)
            if row['status']!='COMMITTED' or row['request_sha256']!=original['request_sha256']:
                raise ValueError('captured_recovery_original_journal_binding')
            return row['result']
        if job('-end')!=original or job('-child')['pid']!=original['child_pid']:
            raise ValueError('captured_recovery_original_child_binding')
        request=self._bridge;key=digest(request)[:40];batch=self.owner.batch()
        if (digest(batch)!=self._batch or not self.owner.correction_reason or
                controller._read('bridge-start-'+key,request)!=dict(state='PREPARED') or
                controller._read('bridge-captured-'+key,request) is not None or
                batch['registrations']!={request['registration']['security']['ticker']:request['registration']} or
                request['registration']['security']['canonical_security_id']!=slot_request['security'] or
                request['session']!=slot_request['session'] or
                any(o['payload']['calendar']['session']!=request['session'] for o in batch['observations'])):
            raise ValueError('captured_recovery_source_binding')
        grant=dict(contract='known-captured-source-recovery-v1',original_attempt=original['attempt'],
            original_request=original['request_sha256'],slot=deepcopy(slot_request),batch=self._batch,
            correction_reason=self.owner.correction_reason,new_provider_HTTP=0,max_new_model_contexts=2,
            retries=0,original_cycle_preserved=True)
        if self._approval(deepcopy(grant))!=digest(grant):
            raise ValueError('captured_recovery_explicit_approval_required')
        return grant


class ManualInitializationRecovery:
    """Live backend capability, not a receipt loader or an automatic retry.

    The reviewer owns transport-specific custody and wait/reaping evidence. It
    supplies original bytes, not a claimed success label. Approval is rechecked
    under the host lease and again in the child. Neither callable comes from JSON.
    """
    def __init__(self, *, config, original_scope, account, packet, frozen_context,
                 review_failure, approval):
        if not callable(review_failure) or not callable(approval):
            raise ValueError('host_recovery_backend_capabilities_required')
        self._scope = deepcopy(original_scope)
        if config.environment != 'test' or config.mode != 'write':
            raise ValueError('host_recovery_isolated_store_required')
        self._store_path, self._store_identity = config.validate()
        self._primary = dict(account=account, security=original_scope['identity']['security'],
            input=digest(dict(packet=packet, context=frozen_context)), **MODEL)
        self._context = deepcopy(frozen_context)
        self._packet_sha256 = digest(packet)
        self._review = review_failure
        self._approval = approval

    def _authorize(self, controller, scope, request, prior):
        if (controller.store.path != self._store_path or controller.store.identity != self._store_identity):
            raise ValueError('host_recovery_store_binding')
        if ({k:v for k,v in scope.items() if k != 'expires_at'} !=
                {k:v for k,v in self._scope.items() if k != 'expires_at'} or
                scope['identity']['frozen_input_sha256'] != self._packet_sha256):
            raise ValueError('host_recovery_original_scope_binding')
        if (not prior or prior.get('state') not in ('COMPLETED_NO_SEND', 'CALLBACK_FAILED') or
                prior.get('request_sha256') != digest(request) or not prior.get('attempt') or
                prior.get('exit') not in (0, 1) or
                prior.get('calendar',{}).get('scope_sha256') != digest(self._scope)):
            raise ValueError('host_recovery_original_terminal_required')
        attempt = prior['attempt']
        ended = controller._read(attempt+'-end', request)
        child = controller._read(attempt+'-child', request)
        if ended != prior or not child or child['pid'] != prior.get('child_pid'):
            raise ValueError('host_recovery_original_process_binding')
        primary = self._primary
        stage = dict(primary, stage='BLIND')
        name = 'daily-primary-'+digest(primary)[:40]+'-blind'
        if (controller._read(name+'-started', stage) != dict(state='IN_FLIGHT') or
                controller._read(name+'-response', stage) is not None):
            raise ValueError('host_recovery_original_primary_required')
        proof = self._review(deepcopy(request), deepcopy(prior), deepcopy(primary))
        evidence = self._check_proof(proof, prior)
        grant = dict(contract='manual-initialization-recovery-v1',
            recovery_store=dict(path=str(self._store_path),identity=list(self._store_identity)),
            original_host_attempt=attempt, original_host_request_sha256=digest(request),
            original_scope_sha256=digest(self._scope),
            recovery_scope_sha256=digest(scope), primary_request_sha256=digest(primary),
            frozen_context=deepcopy(self._context), evidence_sha256=evidence,
            expires_at=scope['expires_at'], max_contexts=2, max_seconds=600,
            max_input_bytes=384*1024, max_output_bytes=128*1024, retries=0)
        approved = self._approval(deepcopy(grant))
        if (not isinstance(approved,str) or len(approved)!=64 or
                any(c not in '0123456789abcdef' for c in approved)):
            raise ValueError('host_recovery_explicit_approval_required')
        return dict(grant, approval_sha256=approved)

    def _check_proof(self, proof, prior):
        if not isinstance(proof,dict) or set(proof) != {
                'started','finished','events','stderr','prompt','schema',
                'wait_observation','output_present','adjudication_started'}:
            raise ValueError('host_recovery_original_bytes_required')
        if any(not isinstance(proof[k],bytes) for k in
               ('started','finished','events','stderr','prompt','schema')):
            raise ValueError('host_recovery_original_bytes_required')
        start, end = json.loads(proof['started']), json.loads(proof['finished'])
        waited = proof['wait_observation']
        if (end.get('status') != 'FAILED_NO_RETRY' or end.get('exit') != 1 or
                type(end.get('pid')) is not int or end['pid'] <= 0 or
                end.get('stage') != 'BLIND' or end.get('attempt') != 1 or end.get('retry') != 0 or
                not isinstance(waited,dict) or waited.get('pid') != end['pid'] or
                waited.get('exit') != end['exit'] or waited.get('reaped') is not True or
                waited.get('parent_pid') != prior['child_pid'] or
                waited.get('timed_out') is not False or
                proof['output_present'] is not False or proof['adjudication_started'] is not False or
                proof['events'].strip() or end.get('usage') != [] or
                end.get('runtime') != dict(metadata_files=[],session=None,turn_contexts=[],verified=False) or
                b'failed to initialize in-process app-server client:' not in proof['stderr']):
            raise ValueError('host_recovery_not_terminal_before_context')
        fields = ('stage','started','attempt','retry','model','effort','packet_sha','prompt_sha','schema_sha')
        if (any(start.get(k) != end.get(k) for k in fields) or start.get('status') != 'STARTED' or
                end['model'] != MODEL['model'] or end['effort'] != MODEL['effort'] or
                end['packet_sha'] != self._packet_sha256 or
                end['prompt_sha'] != digest(proof['prompt']) or
                end['schema_sha'] != digest(json.loads(proof['schema'])) or
                end['schema_sha'] != self._context['schema_sha256'] or
                not end['started'] <= end.get('ended',0) or
                not prior['observed_at'] <= datetime.fromtimestamp(end['started'],timezone.utc).isoformat()):
            raise ValueError('host_recovery_original_artifact_binding')
        return digest({k:digest(v) if isinstance(v,bytes) else v for k,v in proof.items()})

    def _child_resolver(self, controller, scope, request, prior, grant):
        def resolve(primary, packet, context):
            if primary != self._primary or context != self._context or digest(packet) != self._packet_sha256:
                raise ValueError('host_recovery_primary_input_binding')
            if self._authorize(controller, scope, request, prior) != grant:
                raise ValueError('host_recovery_authority_changed')
            expires = datetime.fromisoformat(scope['expires_at']).timestamp()
            evidence = dict(request_sha256=digest(primary), evidence_sha256=grant['evidence_sha256'],
                terminal_before_context=True, actual_contexts=0, outputs=0)
            token = controller.authorize_initialization_recovery(account=primary['account'],
                security=primary['security'], packet=packet, frozen_context=context,
                review_failure=lambda req: deepcopy(evidence) if req==primary else None,
                approval=lambda req,ev: grant['approval_sha256'] if req==primary and ev==evidence else None,
                expires_at=expires)
            def still_authorized():
                if time.time() >= expires or self._authorize(controller, scope, request, prior) != grant:
                    raise ValueError('host_recovery_revoked_or_expired')
            controller._host_recovery_guard = still_authorized
            controller._append('host-recovery-child-primary-'+digest(request)[:40], request,
                dict(state='CHILD_PRIMARY_AUTHORIZED', original_host_attempt=prior['attempt'],
                     primary_request_sha256=digest(primary), grant_sha256=digest(grant), child_pid=os.getpid()))
            return token
        return resolve


def _stop_owned_child(pid, *, unreaped=False):
    """Kill only our unreaped child or the session it created, then reap it."""
    if not unreaped:
        ended, status = os.waitpid(pid, os.WNOHANG)
        if ended:
            return status
    try:
        if os.getpgid(pid) == pid:
            os.killpg(pid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError:
        # macOS can deny a group signal after the child's watchdog has already
        # exited. Reaping is observation, not an alternative signal or bypass.
        ended, status = os.waitpid(pid, os.WNOHANG)
        if ended:
            return status
        raise
    return os.waitpid(pid, 0)[1]


def run_slot(config, *, market, at, watermark, identity, operation=None,
             enabled=False, timeout_seconds=MAX_SECONDS, daily_cycle=False):
    """Supervise one backend callback with a shared lifetime lease and deadline.

    Shorter deadlines are permitted for bounded tests; nothing can exceed 600s.
    `at` is the caller's calendar clock, recorded separately from actual wall time.
    A recovery slot re-enters original controller/Owner checks. It never turns a
    previous transport result or stale outbox row into current accepted authority.
    """
    gate = calendar_gate(market, at, watermark=watermark)
    base = dict(contract=CONTRACT, calendar=gate, send=False, scheduler=False,
                strict_ready=False, host_pid=os.getpid(),
                observed_at=datetime.now(timezone.utc).isoformat())
    if not enabled:
        return dict(base, state='DISABLED_DRY_RUN')
    if gate['state'] != 'SOURCE_CHECK_PLAN':
        return dict(base, state=gate['state'])
    remaining = (datetime.fromisoformat(gate['recovery_deadline']) - at).total_seconds()
    if remaining <= 0:
        return dict(base, state='RECOVERY_WINDOW_CLOSED')
    return _supervise(config, market=market, at=at, gate=gate, base=base,
        identity=identity, operation=operation, timeout_seconds=timeout_seconds,
        remaining=remaining, daily_cycle=daily_cycle)


def run_manual_research(config, *, scope, identity, approval=None, operation=None,
                        enabled=False, timeout_seconds=MAX_SECONDS, initialization_recovery=None,
                        daily_cycle=False, captured_source_recovery=None, execution_profile=ASTRA_XHIGH_V1):
    """Explicit backend-only canary, not a simulated scheduled slot.

    `approval` is a trusted operator capability returning the exact approved
    scope digest, or None after revocation. No JSON receipt issues authority.
    The original callback must still enforce HTTP/Owner/consumer permissions.
    The clock cannot be supplied by a request. A consumed one-shot scope never
    automatically re-enters transport after a failure or unknown outcome.
    """
    at = datetime.now(timezone.utc)
    execution_profile=require_profile(execution_profile)
    if execution_profile!=ASTRA_XHIGH_V1 and (initialization_recovery is not None or captured_source_recovery is not None):
        raise ValueError('legacy_recovery_profile_cannot_be_relabelled')
    if captured_source_recovery is not None and (not daily_cycle or initialization_recovery is not None or
            type(captured_source_recovery) is not CapturedSourceRecovery):
        raise ValueError('captured_recovery_daily_cycle_required')
    base = dict(contract=CONTRACT, mode='MANUAL_RESEARCH_CANARY',
        send=False, scheduler=False, scheduled_slot_pass=False, strict_ready=False,
        host_pid=os.getpid(), observed_at=at.isoformat())
    if not enabled:
        return dict(base, state='DISABLED_DRY_RUN')
    # Recovery approvals run under the bounded host lease review below.
    if not callable(approval) or (initialization_recovery is None and approval() != digest(scope)):
        return dict(base, state='EXPLICIT_MANUAL_SCOPE_REQUIRED')
    if (set(scope) != {'mode','market','session','prior_session','kind','identity','plan_sha256','expires_at'}
            or scope['mode'] != 'MANUAL_RESEARCH_CANARY' or scope['identity'] != identity
            or scope['market'] not in ('kr','us')
            or scope['kind'] not in ('EXISTING_SUBJECT_SUCCESSOR','NEW_SUBJECT_BOOTSTRAP')
            or not isinstance(scope['plan_sha256'],str) or len(scope['plan_sha256']) != 64
            or any(c not in '0123456789abcdef' for c in scope['plan_sha256'])):
        raise ValueError('manual_scope_binding')
    expiry = datetime.fromisoformat(scope['expires_at'])
    if expiry.tzinfo is None:
        raise ValueError('manual_explicit_expiry_required')
    remaining = (expiry-at).total_seconds()
    if remaining <= 0:
        return dict(base, state='MANUAL_SCOPE_EXPIRED')
    from datetime import date
    session = date.fromisoformat(scope['session'])
    latest, calendar = target_session(scope['market'], at)
    if session > latest:
        return dict(base, state='SESSION_NOT_COMPLETED')
    # A completed market date alone cannot prove this exact day was a session.
    from app.services.price_structure_wave_fibonacci_v3_service import _calendar_for_range
    _, trading_calendar = _calendar_for_range(scope['market'].upper(), start=session, end=session)
    if not trading_calendar.is_session(session.isoformat()):
        return dict(base, state='NOT_A_TRADING_SESSION')
    prior = scope['prior_session']
    if scope['kind'] == 'NEW_SUBJECT_BOOTSTRAP':
        if prior is not None:
            raise ValueError('bootstrap_cannot_claim_prior_owner')
    elif prior is None or date.fromisoformat(prior) >= session:
        return dict(base, state='ALREADY_CONSUMED_OR_UNKNOWN_PRIOR')
    gate = dict(state='MANUAL_SOURCE_PLAN', mode='MANUAL_RESEARCH_CANARY',
        market=scope['market'], session=scope['session'], latest_completed=str(latest),
        original_calendar=calendar, slot=None, scheduled_slot_pass=False,
        scope_sha256=digest(scope), plan_sha256=scope['plan_sha256'], kind=scope['kind'],
        prior_session=prior)
    base['calendar'] = gate
    return _supervise(config, market=scope['market'], at=at, gate=gate, base=base,
        identity=identity, operation=operation, timeout_seconds=timeout_seconds,
        remaining=remaining, one_shot=digest({k:v for k,v in scope.items() if k!='expires_at'}),
        approval=approval, approval_digest=digest(scope), recovery=initialization_recovery, scope=scope,
        daily_cycle=daily_cycle, captured_source_recovery=captured_source_recovery,
        execution_profile=execution_profile)


def _supervise(config, *, market, at, gate, base, identity, operation,
               timeout_seconds, remaining, one_shot=None, approval=None, approval_digest=None,
               recovery=None, scope=None, daily_cycle=False, captured_source_recovery=None,
               execution_profile=ASTRA_XHIGH_V1):
    if operation is None:
        return dict(base, state='BACKEND_CAPABILITY_REQUIRED')
    if (not callable(operation) or threading.active_count() != 1 or
            threading.current_thread() is not threading.main_thread()):
        raise ValueError('single_thread_trusted_manual_parent_required')
    if (type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds)
            or not 0 < timeout_seconds <= MAX_SECONDS):
        raise ValueError('host_timeout_must_not_exceed_600s')
    deadline_seconds = min(timeout_seconds, remaining)
    absolute_deadline = time.monotonic() + deadline_seconds
    if (set(identity) != {'account_scope', 'security', 'frozen_input_sha256'} or
            not all(isinstance(v, str) and v for v in identity.values()) or
            len(identity['frozen_input_sha256']) != 64 or
            any(c not in '0123456789abcdef' for c in identity['frozen_input_sha256'])):
        raise ValueError('host_input_scope_required')
    execution_profile=require_profile(execution_profile)
    controller = NoSendController(config, enabled=True,execution_profile=execution_profile)
    lock = plain(str(controller.store.path) + '.no-send-runner.lock')
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    pid = None
    grant = None
    prior_result = None
    alarm_previous = None
    start_read = start_write = None
    worker_pid = None
    guardian_lost = False
    termination_denied = False
    guardian = recovery is not None or daily_cycle
    slot_request = dict(contract=CONTRACT, account_scope=identity['account_scope'],
                        security=identity['security'], market=market, session=gate['session'])
    slot_key = 'daily-cycle-' + digest(slot_request)[:40]
    stopped = False
    def owned_wait(*, stop=False, nonblocking=False):
        nonlocal pid
        # A pending interrupt is delivered only after ownership is cleared.
        # Reaping frees the PID; cleanup must never signal that freed number.
        mask = signal.pthread_sigmask(signal.SIG_BLOCK,
            {signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM})
        try:
            if stop:
                ended, status = pid, _stop_owned_child(pid, unreaped=guardian)
            else:
                ended, status = os.waitpid(pid, os.WNOHANG if nonblocking else 0)
            if ended:
                pid = None
            return ended, status
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, mask)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError('host_lease_alias')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return dict(base, state='OVERLAP_SKIPPED', automatic_retry=False)
        if recovery is not None:
            if signal.getitimer(signal.ITIMER_REAL)[0]:
                raise ValueError('host_recovery_existing_alarm')
            alarm_previous = signal.getsignal(signal.SIGALRM)
            def review_timeout(*_):
                raise TimeoutError('host_recovery_review_deadline')
            signal.signal(signal.SIGALRM, review_timeout)
            signal.setitimer(signal.ITIMER_REAL, max(.001,absolute_deadline-time.monotonic()))
        request = dict(contract=CONTRACT, identity=identity, market=market,
                       session=gate['session'])
        if execution_profile!=ASTRA_XHIGH_V1:
            request['execution_profile']=execution_profile.contract
            base['execution_profile']=execution_profile.contract
        if daily_cycle:
            if controller.account_stopped(identity['account_scope']):
                return dict(base, state='ACCOUNT_STOPPED', automatic_retry=False)
            with controller.store.atomic_job(slot_key, slot_request) as cell:
                if cell['previous'] is not None:
                    if captured_source_recovery is None:
                        return dict(base, state='DAILY_CYCLE_ALREADY_ATTEMPTED', automatic_retry=False,
                            prior_intent=cell['previous']['result'], export_only_recovery=True)
                    if cell['previous']['result']['identity'] != identity:
                        raise ValueError('captured_recovery_original_identity_required')
                else:
                    if captured_source_recovery is not None:
                        raise ValueError('captured_recovery_original_cycle_missing')
                    cell['result'] = dict(state='CYCLE_CONSUMED', identity=identity,
                                          clock=at.isoformat(), wall=base['observed_at'])
            if captured_source_recovery is not None:
                original=controller._read(slot_key+'-done',slot_request)
                # Durable once-only approval is consumed before forking; all
                # original cycle/failed-host records remain immutable.
                with controller.store.atomic_job(slot_key+'-capture-recovery',slot_request) as cell:
                    if cell['previous'] is not None:
                        return dict(base,state='DAILY_CYCLE_ALREADY_ATTEMPTED',automatic_retry=False,
                            export_only_recovery=True,source_recovery_consumed=True)
                    repair=captured_source_recovery.authorize(controller,slot_request,original)
                    cell['result']=dict(state='CAPTURE_REPAIR_CONSUMED',grant=repair)
                base=dict(base,captured_source_recovery_of=original['attempt'],capture_recovery_grant=repair)
        if one_shot:
            request['manual_scope_sha256'] = one_shot
            if approval() != approval_digest:
                return dict(base, state='MANUAL_SCOPE_REVOKED')
            started_key = 'manual-start-' + one_shot[:48]
            done_key = 'manual-done-' + one_shot[:48]
            if captured_source_recovery is not None:
                done_key=slot_key+'-capture-recovery-host-done'
            elif controller._read(started_key, request) is not None:
                prior_result = controller._read(done_key, request)
                if recovery is None:
                    return dict(base, state='MANUAL_ALREADY_ATTEMPTED',
                        prior_host_state=None if prior_result is None else prior_result['state'],
                        prior_result_is_not_current_authority=True, automatic_retry=False)
                if type(recovery) is not ManualInitializationRecovery:
                    raise ValueError('host_recovery_live_capability_required')
                recovery_key = 'recovery-of-'+one_shot[:48]
                # The host lease serializes readers; atomic_job makes consumption
                # durable before fork. A crash after this point spends the right.
                with controller.store.atomic_job(recovery_key, request) as cell:
                    if cell['previous'] is not None:
                        return dict(base, state='RECOVERY_ONCE_CONSUMED', automatic_retry=False,
                                    original_host_attempt=prior_result.get('attempt') if prior_result else None)
                    grant = recovery._authorize(controller, scope, request, prior_result)
                    cell['result'] = dict(state='RECOVERY_INTENT_CONSUMED', grant=grant)
                done_key = recovery_key+'-done'
                base = dict(base, recovery_of=prior_result['attempt'], recovery_grant_sha256=digest(grant))
            else:
                if recovery is not None:
                    raise ValueError('host_recovery_original_attempt_missing')
                controller._append(started_key, request,
                    dict(state='STARTED', wall=base['observed_at'], automatic_retry=False))
        if alarm_previous is not None:
            signal.setitimer(signal.ITIMER_REAL,0)
            signal.signal(signal.SIGALRM,alarm_previous)
            alarm_previous = None
        if recovery is not None:
            deadline_seconds = min(deadline_seconds,absolute_deadline-time.monotonic())
        if deadline_seconds <= 0:
            return dict(base,state='RECOVERY_NO_CHILD_DEADLINE',automatic_retry=False)
        attempt = 'host-' + uuid.uuid4().hex
        started = time.monotonic()
        controller._append(attempt + '-intent', request,
            dict(state='STARTED', host_pid=os.getpid(), slot=gate['slot'],
                 clock=at.isoformat(), wall=base['observed_at'],
                 timeout_seconds=deadline_seconds, max_seconds=MAX_SECONDS,
                 operation=operation.__module__ + '.' + operation.__qualname__))
        if guardian:
            start_read,start_write = os.pipe()
        pid = os.fork()
        if pid == 0:
            is_guardian = False
            try:
                os.setsid()
                # The child retains the lease if the supervisor dies. Its own
                # deadline kills only this newly created process group.
                signal.signal(signal.SIGALRM, lambda *_: os.killpg(os.getpid(), signal.SIGKILL))
                signal.setitimer(signal.ITIMER_REAL, deadline_seconds)
                if guardian:
                    # A living session leader reserves the PGID until cleanup.
                    # It reaps the worker, reports status, then waits for its
                    # parent to terminate this exact owned group. Model children
                    # cannot outlive a dead worker or cause PID-reuse signalling.
                    os.close(start_read)
                    is_guardian = True
                    worker = os.fork()
                    if worker:
                        _,worker_status = os.waitpid(worker,0)
                        os.write(start_write,encoded(dict(pid=worker,status=worker_status))+b'\n')
                        os.close(start_write)
                        while True:signal.pause()
                    is_guardian = False
                    os.close(start_write)
                    signal.signal(signal.SIGALRM,lambda *_: os.killpg(os.getpgrp(),signal.SIGKILL))
                    signal.setitimer(signal.ITIMER_REAL,deadline_seconds)
                child = NoSendController(config, enabled=True,execution_profile=execution_profile)
                if daily_cycle:
                    def check_slot():
                        if child.account_stopped(identity['account_scope']):
                            raise ValueError('account_stop_latched')
                    child._host_slot_guard = check_slot
                    check_slot()
                if one_shot and approval() != approval_digest:
                    raise ValueError('manual_scope_revoked_before_child')
                if captured_source_recovery is not None:
                    if captured_source_recovery.authorize(child,slot_request,original)!=repair:
                        raise ValueError('captured_recovery_grant_changed')
                child._append(attempt + '-child', request,
                              dict(pid=os.getpid(), pgid=os.getpgrp(), state='RUNNING'))
                if grant is not None:
                    if recovery._authorize(child, scope, request, prior_result) != grant:
                        raise ValueError('host_recovery_authority_changed_before_child')
                    child._host_initialization_recovery = recovery._child_resolver(
                        child, scope, request, prior_result, grant)
                result = operation(child, gate)
                child._check_host_recovery()
                if not isinstance(result, dict) or result.get('send') is not False:
                    raise ValueError('no_send_callback_result_required')
                if result.get('input_identity') != identity:
                    raise ValueError('host_callback_input_binding')
                if len(encoded(result)) > MAX_RESULT_BYTES:
                    raise ValueError('host_result_size_bound')
                child._append(attempt + '-response', request, result)
                os._exit(0)
            except BaseException as exc:
                if is_guardian:
                    # Includes a broken report pipe after parent death. Retain
                    # the live PGID until all owned descendants are stopped.
                    os.killpg(os.getpid(), signal.SIGKILL)
                try:
                    code = str(exc)
                    code = code if len(code) <= 150 and code.replace('_', '').isalnum() else 'DETAILS_WITHHELD'
                    NoSendController(config, enabled=True,execution_profile=execution_profile)._append(attempt + '-failure', request,
                        dict(state='CALLBACK_FAILED', error_type=type(exc).__name__, error_code=code))
                finally:
                    os._exit(1)
        observed_child_pid = pid
        if guardian:
            os.close(start_write);start_write = None
            os.set_blocking(start_read,False)
        timed_out = False
        while True:
            report = None
            if guardian:
                try:report = os.read(start_read,512)
                except BlockingIOError:pass
            if report:
                report=json.loads(report)
                worker_pid,status=report['pid'],report['status']
                try:os.killpg(pid,signal.SIGKILL)
                except PermissionError:
                    termination_denied=True
                    controller._append(attempt+'-termination-denied',request,
                        dict(state='OS_TERMINATION_DENIED',guardian_pid=pid,automatic_retry=False))
                    raise
                ended,_ = owned_wait()
            else:
                ended,status=owned_wait(nonblocking=True)
                if ended and guardian:guardian_lost=True
            if ended:
                break
            if daily_cycle and controller.account_stopped(identity['account_scope']):
                _, status = owned_wait(stop=True)
                stopped = True
                break
            if time.monotonic() - started >= deadline_seconds:
                try:
                    _, status = owned_wait(stop=True)
                except PermissionError:
                    termination_denied = True
                    controller._append(attempt + '-termination-denied', request,
                        dict(state='OS_TERMINATION_DENIED', child_pid=pid,
                             no_alternate_signal=True, automatic_retry=False))
                    raise
                timed_out = True
                break
            time.sleep(min(0.02, deadline_seconds / 10))
        guardian_pid = observed_child_pid if guardian else None
        child_pid = worker_pid or observed_child_pid
        elapsed = time.monotonic() - started
        # Child watchdog termination is also a timeout, not a retry permission.
        timed_out |= elapsed >= deadline_seconds
        interrupted = os.WIFSIGNALED(status)
        response = controller._read(attempt + '-response', request)
        failure = controller._read(attempt + '-failure', request)
        state = ('TIMEOUT_REVIEW_REQUIRED' if timed_out else
                 'RECOVERY_GUARDIAN_LOST' if guardian_lost else
                 'INTERRUPTED_REVIEW_REQUIRED' if interrupted else
                 'CALLBACK_FAILED' if os.waitstatus_to_exitcode(status) != 0 else
                 'COMPLETED_NO_SEND' if response is not None else 'UNKNOWN_RESPONSE')
        revoked = False
        if grant is not None:
            try:
                left = absolute_deadline-time.monotonic()
                if left <= 0:
                    raise TimeoutError('host_recovery_final_review_deadline')
                alarm_previous = signal.getsignal(signal.SIGALRM)
                signal.signal(signal.SIGALRM,review_timeout)
                signal.setitimer(signal.ITIMER_REAL,left)
                revoked = approval() != approval_digest
                revoked |= (time.time() >= datetime.fromisoformat(scope['expires_at']).timestamp() or
                            recovery._authorize(controller,scope,request,prior_result) != grant)
                revoked |= time.time() >= datetime.fromisoformat(scope['expires_at']).timestamp()
            except TimeoutError:
                timed_out = True
                state = 'TIMEOUT_REVIEW_REQUIRED'
            except (ValueError,TypeError):
                revoked = True
            finally:
                if alarm_previous is not None:
                    signal.setitimer(signal.ITIMER_REAL,0)
                    signal.signal(signal.SIGALRM,alarm_previous)
                    alarm_previous = None
        else:
            revoked = bool(one_shot and approval() != approval_digest)
        if daily_cycle:
            stopped |= controller.account_stopped(identity['account_scope'])
        if revoked:
            state = 'MANUAL_SCOPE_REVOKED'
        if stopped:
            state = 'ACCOUNT_STOPPED'
        result = dict(base, state=state, attempt=attempt, request_sha256=digest(request),
            child_pid=child_pid, exit=os.waitstatus_to_exitcode(status),
            elapsed_seconds=elapsed, timeout_seconds=deadline_seconds,
            automatic_retry=False, response=None if timed_out or interrupted or revoked or guardian_lost or stopped else response, failure=failure)
        if guardian:
            result['guardian_pid']=guardian_pid
            result['guardian_cleanup']='OWNED_LIVE_SESSION_SIGKILL_THEN_REAP' if worker_pid else 'UNKNOWN_OR_TIMEOUT'
        controller._append(attempt + '-end', request, result)
        if one_shot:
            controller._append(done_key, request, result)
        if daily_cycle:
            controller._append(slot_key+('-capture-recovery-done' if captured_source_recovery else '-done'), slot_request, result)
        return result
    finally:
        for pipe in (start_read,start_write):
            if pipe is not None:os.close(pipe)
        if alarm_previous is not None:
            signal.setitimer(signal.ITIMER_REAL,0)
            signal.signal(signal.SIGALRM,alarm_previous)
        if pid:
            if termination_denied:
                # Do not repeat a denied operation. Await the child's existing
                # self-deadline or normal end; never accept its result here.
                owned_wait()
            else:
                owned_wait(stop=True)
        os.close(fd)
