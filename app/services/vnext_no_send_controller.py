"""Manual, default-disabled public research controller. No scheduling or sending.

The durable journal coordinates trusted backend callbacks, not JSON authority.
Source append re-enters the original Owner; model acceptance re-enters ReviewOwner.
An ambiguous external attempt is never retried automatically, even after restart.
"""
from copy import deepcopy
from datetime import datetime, timedelta
import json
import time
from zoneinfo import ZoneInfo

from app.services.vnext_research_store import digest
from app.services.vnext_research_ingestion import AppendResearchStore
from app.services.vnext_daily_research import UseRegistry, _persistent_registry, stage_state
from app.services.vnext_daily_delta import completed_session
from app.services.vnext_public_capture import target_session
from app.services.unified_runtime_v2 import scheduled_slots
from app.services.vnext_execution_profile import ASTRA_XHIGH_V1, require_profile

CONTRACT = 'isolated-no-send-daily-controller-v1'
MODEL = dict(model='gpt-6-astra', effort='xhigh', timeout_seconds=600, retries=0)


def calendar_gate(market, at, *, watermark=None, provider_state='NOT_CHECKED'):
    if at.tzinfo is None or market not in ('kr', 'us'):
        raise ValueError('explicit_calendar_required')
    local = at.astimezone(ZoneInfo('Asia/Seoul'))
    session = completed_session(market, at)
    latest, original = target_session(market, at)
    slots = scheduled_slots(market, local.date())
    index = next((i for i in reversed(range(3)) if at >= slots[i]), None)
    state = ('WAIT_CALENDAR' if session is None or index is None else
             'NO_NEW_SESSION' if watermark is not None and session <= watermark else
             'SESSION_DONE_PROVIDER_NOT_YET_AVAILABLE' if provider_state == 'NOT_YET_AVAILABLE' else
             provider_state if provider_state in ('EMPTY','REVOKED','DENIED') else 'SOURCE_CHECK_PLAN')
    return dict(state=state, market=market, session=session, latest_completed=str(latest),
        as_of_UTC=at.astimezone(ZoneInfo('UTC')).isoformat(), as_of_KST=local.isoformat(),
        as_of_NY=at.astimezone(ZoneInfo('America/New_York')).isoformat(),
        original_calendar=original, slot=index, slots=[s.isoformat() for s in slots],
        recovery_limit=2, recovery_deadline=(slots[-1]+timedelta(minutes=10)).isoformat(),
        send=False, scheduler=False)


def cycle_identity(*, registration, session, source_generation, correction_epoch,
                   canonical_input_digest):
    sec = registration['security']
    if (not source_generation or not registration['registration_version'] or
            not canonical_input_digest or not isinstance(correction_epoch, str)):
        raise ValueError('complete_cycle_identity_required')
    return dict(contract=CONTRACT, market=sec['country'], exchange=sec['exchange'],
        security=sec['canonical_security_id'], session=session,
        registration_version=registration['registration_version'], source_generation=source_generation,
        correction_epoch=correction_epoch, canonical_input_digest=canonical_input_digest)


def cycle_from_packet(*, registration, packet, correction_epoch):
    """Bind to the owned price packet, never to optional technical generations.

    This constructs an identity only. Finalization still independently consumes
    the live source and accepted-stage owners before writing an outbox entry.
    """
    base = packet['base']
    sessions = {e['data']['calendar']['session'] for e in base['evidence']
                if e['field'] == 'completed_close'}
    if len(sessions) != 1 or base['public_security'] != registration['security']:
        raise ValueError('outbox_exact_price_packet_required')
    return cycle_identity(registration=registration, session=next(iter(sessions)),
        source_generation=base['run_id'], correction_epoch=correction_epoch,
        canonical_input_digest=digest(packet))


class NoSendController:
    def __init__(self, config, *, enabled=False, execution_profile=ASTRA_XHIGH_V1):
        if config.environment != 'test' or config.mode != 'write':
            raise ValueError('isolated_public_controller_only')
        self.store = AppendResearchStore(config)
        self.config = config
        self.enabled = enabled
        self.execution_profile = require_profile(execution_profile)
        self._initialization_recoveries = {}
        self._host_initialization_recovery = None
        self._host_recovery_guard = None
        self._host_slot_guard = None

    def _check_host_recovery(self):
        if self._host_slot_guard is not None:
            self._host_slot_guard()
        if self._host_recovery_guard is not None:
            self._host_recovery_guard()

    def stop_participating_account(self, account_scope):
        """Sticky cooperative STOP, never an account-wide remote-service claim."""
        if not self.enabled or not isinstance(account_scope, str) or not account_scope:
            raise ValueError('stop_account_scope_required')
        request = dict(contract=CONTRACT, account_scope=account_scope)
        return self._append('account-stop-' + digest(request)[:40], request, dict(state='STOP'))

    def account_stopped(self, account_scope):
        request = dict(contract=CONTRACT, account_scope=account_scope)
        return self._read('account-stop-' + digest(request)[:40], request) is not None

    def authorize_initialization_recovery(self, *, account, security, packet, frozen_context,
                                          review_failure, approval, expires_at):
        """Trusted backend callbacks only; never a public receipt rehydration API.

        The transport-specific reviewer must prove terminal initialization failure
        before any model context. The original ambiguous journal stays immutable.
        One explicit authorization can add one invocation, never automatic retries.
        """
        if self.execution_profile!=ASTRA_XHIGH_V1:
            raise ValueError('legacy_primary_recovery_profile_required')
        request = dict(account=account, security=security,
                       input=digest(dict(packet=packet, context=frozen_context)), **MODEL)
        key = digest(request)[:40]
        if (not self.enabled or not callable(review_failure) or not callable(approval) or
                not time.time() < expires_at <= time.time() + MODEL['timeout_seconds']):
            raise ValueError('initialization_recovery_authority_required')
        stage_request = dict(request, stage='BLIND')
        name = 'daily-primary-'+key+'-blind'
        if (self._read(name+'-started', stage_request) != dict(state='IN_FLIGHT') or
                self._read(name+'-response', stage_request) is not None):
            raise ValueError('initialization_recovery_prior_state')
        evidence = review_failure(deepcopy(request))
        required = {'request_sha256', 'evidence_sha256', 'terminal_before_context',
                    'actual_contexts', 'outputs'}
        if (not isinstance(evidence, dict) or set(evidence) != required or
                evidence['request_sha256'] != digest(request) or
                evidence['terminal_before_context'] is not True or
                evidence['actual_contexts'] != 0 or evidence['outputs'] != 0 or
                not isinstance(evidence['evidence_sha256'], str) or
                len(evidence['evidence_sha256']) != 64 or
                any(c not in '0123456789abcdef' for c in evidence['evidence_sha256'])):
            raise ValueError('initialization_recovery_unproven')
        approved = approval(deepcopy(request), deepcopy(evidence))
        if (not isinstance(approved, str) or len(approved) != 64 or
                any(c not in '0123456789abcdef' for c in approved)):
            raise ValueError('initialization_recovery_explicit_approval_required')
        scope = dict(request_sha256=digest(request), evidence=evidence,
                     approval_sha256=approved, maximum_additional_invocations=1)
        # Same original invocation has one immutable recovery scope across restarts.
        self._append('daily-primary-initialization-recovery-'+key, request, scope)
        token = object()
        self._initialization_recoveries[token] = (deepcopy(request), digest(scope), expires_at)
        return token

    def advance(self, *, market, at, watermark, owner=None, registry=None,
                provider_state='NOT_CHECKED', fail_at=None):
        gate = calendar_gate(market, at, watermark=watermark, provider_state=provider_state)
        if not self.enabled:
            return dict(gate, state='DISABLED_DRY_RUN')
        if gate['state'] != 'SOURCE_CHECK_PLAN':
            return gate
        if at > datetime.fromisoformat(gate['recovery_deadline']):
            return dict(gate, state='RECOVERY_WINDOW_CLOSED')
        if owner is None:
            return dict(gate, state='CAPTURE_AUTHORIZATION_REQUIRED')
        batch = owner.batch()
        if any(r['security']['country'].lower() != market for r in batch['registrations'].values()) or any(
                o['payload']['calendar']['session'] != gate['session'] for o in batch['observations']):
            raise ValueError('controller_completed_session_binding')
        return dict(self.source(owner=owner, registry=registry, fail_at=fail_at), calendar=gate)

    def _read(self, name, request):
        with self.store.connect() as c:
            row = c.execute('SELECT value FROM research_meta WHERE key=?',
                            ('vnext-runtime-v1:job:'+name,)).fetchone()
        if row is None:
            return None
        record = json.loads(row[0])
        if record['request_sha256'] != digest(request) or record['status'] != 'COMMITTED':
            raise ValueError('controller_journal_binding')
        return record['result']

    def _append(self, name, request, result):
        with self.store.atomic_job(name, request) as cell:
            new = cell['previous'] is None
            if not new and cell['previous']['result'] != result:
                raise ValueError('controller_journal_conflict')
            cell['result'] = result
        return new

    def source(self, *, owner, registry, fail_at=None):
        from app.services.vnext_incremental_ingestion import DailyDeltaOwner, run_delta_cycle
        if not self.enabled:
            return dict(state='DISABLED_DRY_RUN', HTTP=0, model=0, send=False)
        if not isinstance(owner, DailyDeltaOwner) or not isinstance(registry, UseRegistry):
            raise ValueError('original_delta_and_use_owners_required')
        batch = owner.batch()
        request = dict(contract=CONTRACT, batch=digest(batch), uses=registry.fingerprint())
        key = digest(request)[:40]
        self._append('daily-source-intent-'+key, request, dict(state='OWNER_VALIDATED'))
        if fail_at == 'BEFORE_APPEND':
            raise RuntimeError('injected_before_append')
        # The original append/cold path is idempotent across a committed crash.
        result = run_delta_cycle(self.config, owner=owner, registry=registry, phase='RECOVER')
        if fail_at == 'AFTER_APPEND':
            raise RuntimeError('injected_after_append')
        receipt = dict(state='COLD_COMPOSITE_READY', packets={k:digest(p) for k,p in result['packets'].items()})
        self._append('daily-source-cold-'+key, request, receipt)
        return dict(receipt, result=result, send=False)

    def classify(self, packet, *, registration, registry, prior=None):
        _persistent_registry(self.store, registry)
        stages = stage_state(packet, registration, registry)
        review = prior.review(packet, registry=registry, registration=registration) if prior else dict(
            reusable=False, status='PRIOR_RESULT_DEPENDENCY_UNVERIFIED')
        return dict(state='REUSE_VALID_PRIOR' if review['reusable'] else 'MODEL_PENDING',
            stages=stages, model_dependency=review, source_current=False,
            release_discovery='NOT_CHECKED', actual_model_calls=0, strict_ready=False)

    def primary(self, *, account, security, packet, frozen_context=None, approved_input_digest=None,
                invoke=None, fail_at=None, initialization_recovery=None):
        """Backend-only runner; approval must bind the entire frozen prompt input.

        Stored responses are transport evidence, not accepted model judgments.
        No PID timeout or expired lease authorizes repeating an ambiguous call.
        """
        if self.execution_profile!=ASTRA_XHIGH_V1:
            raise ValueError('sol_profile_requires_versioned_stage_controller')
        frozen = dict(packet=packet, context=frozen_context)
        request = dict(account=account, security=security, input=digest(frozen), **MODEL)
        if not account or not security:
            raise ValueError('primary_account_security_required')
        if 'base' in packet and packet['base']['public_security']['canonical_security_id'] != security:
            raise ValueError('primary_input_security_mismatch')
        required = {'schema_sha256', 'prompt_builder_sha256', 'knowledge_sha256'}
        if (not self.enabled or not isinstance(frozen_context,dict) or set(frozen_context)!=required or
                any(not isinstance(v,str) or len(v)!=64 or any(c not in '0123456789abcdef' for c in v)
                    for v in frozen_context.values()) or
                approved_input_digest != digest(frozen) or not callable(invoke)):
            return dict(state='MODEL_PENDING', actual_attempts=0, outputs={})
        if self._host_initialization_recovery is not None:
            if initialization_recovery is not None:
                raise ValueError('host_recovery_cannot_replace_inner_capability')
            initialization_recovery = self._host_initialization_recovery(
                deepcopy(request), deepcopy(packet), deepcopy(frozen_context))
        if initialization_recovery is not None:
            try:
                bound = self._initialization_recoveries.get(initialization_recovery)
            except TypeError:
                bound = None
            if bound is None or bound[0] != request or time.time() >= bound[2]:
                raise ValueError('initialization_recovery_binding')
            request = dict(request, initialization_recovery=bound[1])
        key = digest(request)[:40]
        outputs = {}; attempts = 0
        for stage in ('BLIND', 'ADJUDICATION'):
            self._check_host_recovery()
            stage_request = dict(request, stage=stage)
            name = 'daily-primary-'+key+'-'+stage.lower()
            done = self._read(name+'-response', stage_request)
            if done is not None:
                if digest(done['output']) != done['output_sha256']:
                    raise ValueError('primary_response_corrupt')
                outputs[stage] = done['output']
                if done.get('timed_out'):
                    return dict(state='TIMEOUT_RESPONSE_REVIEW_REQUIRED', outputs=outputs,
                                actual_attempts=attempts, automatic_retry=False)
                continue
            claimed = self._append(name+'-started', stage_request, dict(state='IN_FLIGHT'))
            if not claimed:
                return dict(state='UNKNOWN_IN_FLIGHT', stage=stage, outputs=outputs,
                            actual_attempts=attempts, automatic_retry=False)
            attempts += 1
            started = time.monotonic()
            output = invoke(stage, deepcopy(packet), deepcopy(outputs))
            self._check_host_recovery()
            if fail_at == 'AFTER_CALL_BEFORE_SAVE':
                raise RuntimeError('injected_unknown_external_result')
            timed_out = time.monotonic() - started > MODEL['timeout_seconds']
            self._append(name+'-response', stage_request,
                         dict(output=output, output_sha256=digest(output), state='RESPONSE_SAVED',timed_out=timed_out))
            outputs[stage] = output
            if timed_out:
                return dict(state='TIMEOUT_RESPONSE_REVIEW_REQUIRED', outputs=outputs,
                            actual_attempts=attempts, automatic_retry=False)
            if fail_at == 'AFTER_'+stage:
                raise RuntimeError('injected_after_'+stage.lower())
        return dict(state='RESPONSES_SAVED_VALIDATION_REQUIRED', outputs=outputs,
                    actual_attempts=attempts, accepted=False)

    def finalize(self, *, cycle, packet, owner, registry, registration, prompts, fail_at=None):
        from app.services.vnext_model_dependencies import WholeVerdictDependencies
        from app.services.vnext_optional_fy1_research import ReviewOwner
        if not self.enabled or not isinstance(owner, ReviewOwner):
            raise ValueError('original_model_owner_required')
        self._check_host_recovery()
        _persistent_registry(self.store, registry)
        bound = WholeVerdictDependencies(owner, registration=registration, prompts=prompts)
        checked = bound.consume(packet['base'], registry=registry, registration=registration)
        receipt = owner.issue()
        owner.consume(receipt, packet=packet)
        base = packet['base']
        sessions = {e['data']['calendar']['session'] for e in base['evidence'] if e['field']=='completed_close'}
        if (cycle['contract'] != CONTRACT or cycle['session'] not in sessions or
                cycle['source_generation'] != base['run_id'] or
                cycle['market'] != registration['security']['country'] or
                cycle['exchange'] != registration['security']['exchange'] or
                cycle['canonical_input_digest'] != digest(packet) or
                cycle['security'] != registration['security']['canonical_security_id'] or
                cycle['registration_version'] != registration['registration_version']):
            raise ValueError('outbox_cycle_binding')
        result = dict(state='NO_SEND_READY', rendered=checked['rendered'],
            validated_receipt=dict(receipt), source_as_of=packet['base']['as_of'],
            actual_holdings_used=False, strict_ready=False, send=False)
        self._check_host_recovery()
        if fail_at == 'BEFORE_MESSAGE':
            raise RuntimeError('injected_before_message')
        self._append('daily-outbox-'+digest(cycle)[:40], cycle, result)
        return result


def physical_accounting(events):
    """Count attempted requests including auth and failures, not storage rows."""
    counts = dict(provider_total_HTTP=len(events), auth_HTTP=0, identity_HTTP=0,
        chart_HTTP=0, completed_close_HTTP=0, financial_statement_HTTP=0, other_HTTP=0)
    for e in events:
        kind = ('auth' if e.get('auth') else 'identity' if e.get('api') in ('usa10099','ka10099') else
                'chart' if e.get('api') in ('usa06012','usa06013','usa06014','ka10081','ka10082','ka10083') else
                'completed_close' if e.get('api') == 'usa20590' else
                'financial_statement' if e.get('provider') in ('SEC','OpenDART') else 'other')
        counts[kind+'_HTTP'] += 1
    return counts
