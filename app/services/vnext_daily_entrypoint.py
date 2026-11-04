"""Daily adapter to the existing host/bridge, without new transport authority.

Current parent discovery and historic accepted research stay separate. This
entrypoint can consume exact prior whole judgments; fresh acquisition/inference
still requires a separately reviewed backend producer/Primary integration.
"""
from datetime import datetime, timezone
from copy import deepcopy

from app.services.vnext_daily_bridge import DailyResearchBridge
from app.services.vnext_no_send_controller import calendar_gate
from app.services.vnext_completion_export import publish_completion
from app.services.vnext_research_ingestion import AppendResearchStore
from app.services.vnext_research_store import digest

CONTRACT = 'daily-no-send-entrypoint-v1'
PARENT_STATES = {'NOT_CHECKED', 'EMPTY', 'DENIED', 'REVOKED', 'OWNER_ACCEPTED', 'PENDING'}


class FreshDailyAuthority:
    """Live operator/backend capability for one isolated daily execution.

    The trusted producer owns physical quotas and original Owner issuance. The
    approval and parent review callbacks cannot be supplied by JSON or a CLI.
    This capability grants neither source quality nor economic acceptance.
    """
    def __init__(self, *, config, bridge, context, plan, approval, review_parents,
                 expires_at, prior_context=None, captured_source_recovery=None):
        from app.services.vnext_no_send_runner import CapturedSourceRecovery
        if captured_source_recovery is not None and type(captured_source_recovery) is not CapturedSourceRecovery:
            raise ValueError('fresh_daily_original_capture_recovery_required')
        if (type(bridge) is not DailyResearchBridge or not callable(approval) or
                not callable(review_parents) or config.environment != 'test' or config.mode != 'write'):
            raise ValueError('fresh_daily_trusted_backend_required')
        if (digest(plan) != bridge.request['plan_sha256'] or plan.get('retries') != 0 or
                plan.get('model_max') not in (0, 2) or plan.get('seconds') != 600 or
                plan.get('send') is not False or plan.get('HTTP_max',0) <= 0 or
                (not callable(bridge.capture_source) if captured_source_recovery is None else bridge.capture_source is not None) or
                bridge.recovery_source_config is not None or
                plan.get('model_max') and not callable(bridge.primary)):
            raise ValueError('fresh_daily_exact_plan_required')
        if datetime.fromisoformat(expires_at).tzinfo is None:
            raise ValueError('fresh_daily_explicit_expiry_required')
        self._store = config.validate()
        self._bridge = bridge
        self._request = deepcopy(bridge.request)
        self._callbacks = (bridge.capture_source, bridge.primary, bridge.recover_source, bridge.prior_review)
        self.context, self.prior_context = deepcopy(context), deepcopy(prior_context)
        self.plan = deepcopy(plan)
        self.expires_at = expires_at
        self._approval, self._parents = approval, review_parents
        self._scheduled_guard = None
        self.captured_source_recovery=captured_source_recovery
        self._recovery=captured_source_recovery
        self.capture, self.primary = captured_source_recovery is None, plan['model_max'] == 2
        self.grant = dict(contract='fresh-daily-backend-grant-v1', plan_sha256=digest(plan),
            store=dict(path=str(self._store[0]),identity=list(self._store[1])),
            bridge=deepcopy(self._request),context=deepcopy(context),expires_at=expires_at,
            no_send=True, scheduler=False, max_contexts=plan['model_max'],capture=self.capture)
        self._pin = digest(self.grant)

    def check(self, config, bridge):
        if (config.validate() != self._store or bridge is not self._bridge or
                bridge.request != self._request or
                self._callbacks != (bridge.capture_source,bridge.primary,bridge.recover_source,bridge.prior_review) or
                digest(self.plan) != self._request['plan_sha256'] or self.context != self.grant['context'] or
                digest(self.grant) != self._pin or self.expires_at != self.grant['expires_at'] or
                self.captured_source_recovery is not self._recovery or
                self.capture != self.grant['capture'] or self.primary != (self.plan['model_max']==2)):
            raise ValueError('fresh_daily_capability_binding')
        remaining=(datetime.fromisoformat(self.expires_at)-datetime.now(timezone.utc)).total_seconds()
        if not 0 < remaining <= 600 or self._approval(deepcopy(self.grant)) != self._pin:
            raise ValueError('fresh_daily_expired_or_revoked')
        if self._scheduled_guard is not None:
            self._scheduled_guard()
        return self._pin

    def parents(self, config, bridge, packet, stages):
        self.check(config,bridge)
        value=self._parents(deepcopy(packet),bridge.registry)
        if not isinstance(value,dict) or set(value) != {'market','release'}:
            raise ValueError('fresh_daily_parent_contract')
        blocked=set()
        for row in value.values():
            if (set(row) != {'state','watermark','required_for','original_contract','receipt_sha256'} or
                    row['state'] not in PARENT_STATES or not isinstance(row['required_for'],list) or
                    set(row['required_for'])-set(stages) or not row['original_contract']):
                raise ValueError('fresh_daily_parent_contract')
            if row['state'] in ('OWNER_ACCEPTED','EMPTY') and not row['receipt_sha256']:
                raise ValueError('fresh_daily_parent_original_receipt_required')
            if row['state'] not in ('OWNER_ACCEPTED','EMPTY'):
                blocked.update(row['required_for'])
        return dict(parents=deepcopy(value),blocked_stages=sorted(blocked),
            review_sha256=digest(value),full_market_authority=False)

    def prior_matches(self, previous):
        if self.prior_context != self.context:
            return False
        return all(s['execution']['schema_sha']==self.context['schema_sha256']
            for s in previous[0].dependency_record()['stages'].values())


def content_identity(*, bridge, packet, context, parents):
    if not isinstance(bridge, DailyResearchBridge):
        raise ValueError('daily_entrypoint_original_bridge_required')
    if (set(context) != {'schema_sha256','prompt_builder_sha256','knowledge_sha256'} or
            any(not isinstance(v,str) or len(v)!=64 or any(c not in '0123456789abcdef' for c in v)
                for v in context.values())):
        raise ValueError('daily_entrypoint_context_required')
    if (set(parents) != {'market', 'release'} or
            any(not isinstance(p,dict) or p.get('state') not in PARENT_STATES for p in parents.values())):
        raise ValueError('daily_entrypoint_parent_states')
    sec = bridge.registration['security']
    if packet['base']['public_security']['canonical_security_id'] != sec['canonical_security_id']:
        raise ValueError('daily_entrypoint_packet_security')
    return deepcopy(dict(contract=CONTRACT, security=sec, registration=bridge.registration['registration_version'],
        completed_session=bridge.session, prior_session=bridge.prior_session,
        source_plan=bridge.request['plan_sha256'], packet_sha256=digest(packet), context=context,
        parent_watermarks=parents, whole_verdict_only=True, mode='NO_SEND_RESEARCH_REUSE'))


def run_daily(config, *, bridge, packet, context, parents, account_scope, watermark,
              output_root, prior_context=None, enabled=False, at=None, simulation=False, timeout_seconds=600,
              fresh_authority=None, scheduled_event=None):
    """Real host child + cold Owner consumption, or a precise non-execution gate.

    The injected calendar clock is explicit test provenance. No JSON label can
    enable HTTP, AI, scheduler or delivery. Same-cycle fallback is export-only.
    """
    from app.vnext_worker import run_daily_research
    if at is not None and not simulation:
        raise ValueError('injected_clock_requires_simulation_label')
    if scheduled_event is not None:
        from app.services.vnext_one_shot_schedule import ScheduledDailyEvent
        if type(scheduled_event) is not ScheduledDailyEvent or fresh_authority is None or simulation or at is not None:
            raise ValueError('scheduled_live_event_and_separate_source_authority_required')
    if fresh_authority is not None:
        if type(fresh_authority) is not FreshDailyAuthority or simulation or at is not None:
            raise ValueError('fresh_daily_actual_clock_capability_required')
        return _run_fresh(config,bridge=bridge,packet=packet,context=context,parents=parents,
            account_scope=account_scope,output_root=output_root,enabled=enabled,
            timeout_seconds=timeout_seconds,authority=fresh_authority,scheduled_event=scheduled_event)
    observed = datetime.now(timezone.utc)
    clock = at if at is not None else observed
    identity_content = content_identity(bridge=bridge, packet=packet, context=context, parents=parents)
    market = bridge.registration['security']['country'].lower()
    calendar = calendar_gate(market, clock, watermark=watermark)
    base = dict(contract=CONTRACT, clock_kind='SIMULATED_SLOT' if simulation else 'ACTUAL_WALL_CLOCK',
        observed_at=observed.isoformat(), calendar=calendar, content_sha256=digest(identity_content),
        parents=parents, parent_states_are_not_authority=True, send=False, scheduler=False,
        scheduled_wall_clock_pass=False, strict_ready=False, provider_HTTP=0, new_model_contexts=0)
    if not enabled:
        return dict(base, state='DISABLED_DRY_RUN')
    if calendar['state'] != 'SOURCE_CHECK_PLAN':
        return dict(base, state='CALENDAR_WAIT' if calendar['state']=='WAIT_CALENDAR' else calendar['state'])
    if clock >= datetime.fromisoformat(calendar['recovery_deadline']):
        return dict(base, state='RECOVERY_WINDOW_CLOSED')
    if calendar['session'] != bridge.session:
        return dict(base, state='SOURCE_PENDING', reason='CURRENT_SESSION_OWNER_REQUIRED')
    if bridge.prior_review is None:
        return dict(base, state='MODEL_PENDING', reason='FRESH_PRIMARY_APPROVAL_AND_CURRENT_PARENTS_REQUIRED')
    from app.services.vnext_model_dependencies import WholeVerdictDependencies
    from app.services.vnext_daily_research import _persistent_registry
    # Re-entry must check current revocation, not trust an old publication.
    store = AppendResearchStore(config)
    _persistent_registry(store, bridge.registry)
    prior_owner, prompts = bridge.prior_review()
    record = prior_owner.dependency_record()
    if (prior_context != context or any(
            s['execution']['schema_sha'] != context['schema_sha256'] for s in record['stages'].values())):
        return dict(base, state='MODEL_PENDING', reason='FROZEN_PRIOR_CONTEXT_MISMATCH')
    if record['packet'] != packet:
        return dict(base, state='MODEL_PENDING', reason='WHOLE_PACKET_CHANGED_NO_STAGE_SPLICE')
    dependencies = WholeVerdictDependencies(prior_owner, registration=bridge.registration, prompts=prompts)
    eligibility = dependencies.review(packet['base'], registry=bridge.registry, registration=bridge.registration)
    if not eligibility['reusable']:
        return dict(base, state='SOURCE_DENIED' if eligibility['status']=='REVOKED_DEPENDENCY' else 'MODEL_PENDING',
            reason=eligibility['status'], model_dependency=eligibility)
    identity = dict(account_scope=account_scope,
        security=bridge.registration['security']['canonical_security_id'], frozen_input_sha256=digest(identity_content))
    host = run_daily_research(config, bridge=bridge, identity=identity, market=market, at=clock,
        watermark=watermark, enabled=True, timeout_seconds=timeout_seconds, daily_cycle=True,
        allow_capture=False, allow_primary=False, expected_packet_sha256=digest(packet))
    if host['state']=='DAILY_CYCLE_ALREADY_ATTEMPTED':
        # Only the same immutable host result is republished. No owner callback
        # or transport is invoked by completion recovery after a committed crash.
        request = dict(contract='isolated-no-send-host-runner-v1', account_scope=account_scope,
            security=identity['security'], market=market, session=bridge.session)
        from app.services.vnext_no_send_controller import NoSendController
        prior = NoSendController(config)._read('daily-cycle-'+digest(request)[:40]+'-done', request)
        if prior is None:
            return dict(base, state='MODEL_IN_FLIGHT', host=host, reason='PRIOR_OUTCOME_UNKNOWN_NO_RETRY')
        if prior['response'] is None or prior['response'].get('input_identity') != identity:
            return dict(base, state='SOURCE_DENIED', host=host, reason='CONSUMED_CYCLE_NOT_REUSABLE_FOR_CHANGED_INPUT')
        if NoSendController(config).account_stopped(account_scope):
            return dict(base, state='ACCOUNT_STOPPED', host=host)
        host = prior
    if host['state'] != 'COMPLETED_NO_SEND':
        return dict(base, state=host['state'], host=host)
    with store.connect() as conn:
        rows = list(conn.execute('SELECT key,value FROM research_meta'))
    response = host['response']
    try:
        publication = publish_completion(output_root, host=host, rows=rows)
    except (ValueError, OSError) as exc:
        return dict(base, state='COMPLETION_EXPORT_PARTIAL', host=host,
            model_state=response.get('model_state'), reason='REQUIRES_POSTPROCESS',
            export_error_type=type(exc).__name__, export_only_recovery=True)
    return dict(base, state=publication['state'], host=host, publication=publication,
        model_state=response.get('model_state'), original_owner_consumed=response.get('model_reused',False),
        current_source_authority=False, mode='MANUAL_SHADOW',
        activation_blockers=['CURRENT_MARKET_RELEASE_OWNER', 'ACCOUNT_WIDE_PARTICIPATION',
                             'SCHEDULER_AND_SHARED_STORE_AUTHORIZATION', 'SEND_AUTHORIZATION'])


def _run_fresh(config, *, bridge, packet, context, parents, account_scope, output_root,
               enabled, timeout_seconds, authority, scheduled_event=None):
    from app.vnext_worker import run_daily_research
    from app.services.vnext_no_send_controller import NoSendController
    from app.services.vnext_daily_research import _persistent_registry
    from app.services.vnext_model_dependencies import WholeVerdictDependencies
    from app.services.vnext_daily_bridge import cold_packet
    content=content_identity(bridge=bridge,packet=packet,context=context,parents=parents)
    content['mode']='NO_SEND_FRESH_DAILY'
    base=dict(contract=CONTRACT,clock_kind='MANUAL_ACTUAL_CLOCK',send=False,scheduler=False,
        scheduled_wall_clock_pass=False,strict_ready=False,observed_at=datetime.now(timezone.utc).isoformat(),
        content_sha256=digest(content),parents=parents,parent_states_are_not_authority=True)
    if not enabled:
        return dict(base,state='DISABLED_DRY_RUN',provider_HTTP=0,new_model_contexts=0)
    authority.check(config,bridge)
    if context != authority.context or parents != authority.plan.get('parents'):
        raise ValueError('fresh_daily_context_binding')
    market=bridge.registration['security']['country'].lower()
    identity=dict(account_scope=account_scope,security=bridge.registration['security']['canonical_security_id'],
        frozen_input_sha256=digest(content))
    scope=dict(mode='MANUAL_RESEARCH_CANARY',market=market,session=bridge.session,
        prior_session=bridge.prior_session,kind='EXISTING_SUBJECT_SUCCESSOR',identity=identity,
        plan_sha256=bridge.request['plan_sha256'],expires_at=authority.expires_at)
    common=dict(execution_authority=authority,allow_capture=authority.capture,allow_primary=authority.primary,
        enabled=True,timeout_seconds=timeout_seconds,daily_cycle=True)
    if scheduled_event is None:
        host=run_daily_research(config,bridge=bridge,identity=identity,manual_scope=scope,
            approval=lambda:digest(scope) if authority.check(config,bridge) else None,
            captured_source_recovery=authority.captured_source_recovery,**common)
    else:
        if authority.captured_source_recovery is not None:
            raise ValueError('scheduled_source_recovery_requires_separate_review')
        receipt=scheduled_event.check(config,bridge,account_scope,authority)
        authority._scheduled_guard=scheduled_event._validate
        # The original scheduled calendar/guardian owns execution, not the manual
        # adapter. Source and Primary retain their own live permission checks.
        base.update(clock_kind='OS_SCHEDULED_ACTUAL_CLOCK',scheduler=True,
            scheduled_wall_clock_pass=True,scheduler_event=receipt)
        host=run_daily_research(config,bridge=bridge,identity=identity,market=market,
            at=datetime.now(timezone.utc),watermark=bridge.prior_session,**common)
    controller=NoSendController(config)
    if host['state']=='DAILY_CYCLE_ALREADY_ATTEMPTED':
        request=dict(contract='isolated-no-send-host-runner-v1',account_scope=account_scope,
            security=identity['security'],market=market,session=bridge.session)
        key='daily-cycle-'+digest(request)[:40]
        prior=(controller._read(key+'-capture-recovery-done',request) or controller._read(key+'-done',request))
        if prior is None:
            return dict(base,state='MODEL_IN_FLIGHT',host=host,reason='PRIOR_OUTCOME_UNKNOWN_NO_RETRY')
        if (prior.get('response') or {}).get('input_identity') != identity:
            return dict(base,state='SOURCE_DENIED',host=host,reason='CONSUMED_CYCLE_CHANGED_INPUT')
        if controller.account_stopped(account_scope):
            return dict(base,state='ACCOUNT_STOPPED',host=host)
        # Revalidate the already committed original source and whole Owner. This
        # never invokes capture or Primary, including after a partial export.
        _persistent_registry(controller.store,bridge.registry)
        source=bridge.recover_source()
        if source is None or bridge.prior_review is None:
            return dict(base,state='SOURCE_PENDING',host=host,reason='COLD_OWNER_REQUIRED_NO_RETRY')
        current,_=cold_packet(config,registration=bridge.registration,as_of=source.as_of,
            source_generation=source.batch()['runs'][0]['run_id'],reference_owners=bridge.reference_owners)
        review,prompts=bridge.prior_review()
        bound=WholeVerdictDependencies(review,registration=bridge.registration,prompts=prompts)
        from app.services.vnext_daily_research import stage_state
        parent_check=authority.parents(config,bridge,current,stage_state(current['base'],bridge.registration,bridge.registry))
        if (digest(current)!=prior['response'].get('packet_sha256') or
                review.dependency_record()['packet'] != current or
                parent_check != prior['response'].get('current_parent_review') or
                parent_check['blocked_stages'] or
                not bound.review(current['base'],registry=bridge.registry,registration=bridge.registration)['reusable']):
            return dict(base,state='SOURCE_DENIED',host=host,reason='COLD_WHOLE_OWNER_NOT_REUSABLE')
        host=prior
    if host['state']!='COMPLETED_NO_SEND':
        return dict(base,state=host['state'],host=host)
    with controller.store.connect() as conn:
        rows=list(conn.execute('SELECT key,value FROM research_meta'))
    try:
        publication=publish_completion(output_root,host=host,rows=rows)
    except (ValueError,OSError) as exc:
        return dict(base,state='COMPLETION_EXPORT_PARTIAL',host=host,export_only_recovery=True,
            reason='REQUIRES_POSTPROCESS',export_error_type=type(exc).__name__)
    response=host['response']
    return dict(base,state=publication['state'],host=host,publication=publication,
        model_state=response.get('model_state'),new_model_contexts=response.get('model_new',0),
        source_delta_inserts=response.get('source_delta_inserts'),current_source_authority='ORIGINAL_OWNER_RESEARCH_ONLY',
        current_parents=response.get('current_parent_review'),
        activation_blockers=['SCHEDULER_AUTHORIZATION','SEND_AUTHORIZATION'])
