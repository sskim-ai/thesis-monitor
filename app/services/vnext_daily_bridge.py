"""Trusted daily source-to-research bridge, isolated and no-send only.

Factories are backend capabilities, never import paths or public JSON. Recovery
can replay already captured bytes, but an uncertain capture cannot be repeated.
The existing whole model Owner remains the sole accepted research authority.
"""
from datetime import date
from copy import deepcopy
import json

from app.services.vnext_composite_research import CompositeView, reduce_field_state
from app.services.vnext_codex_research import numeric_catalog
from app.services.vnext_daily_research import (
    UseRegistry, _counts, _persistent_registry, compact_message, stage_actions, stage_state,
)
from app.services.vnext_incremental_ingestion import DailyDeltaOwner
from app.services.vnext_model_dependencies import WholeVerdictDependencies
from app.services.vnext_no_send_controller import cycle_identity, CONTRACT as CONTROLLER_CONTRACT
from app.services.vnext_optional_fy1_research import ReviewOwner, attach
from app.services.vnext_price_zones import build_price_attachment, numeric_price_catalog
from app.services.vnext_research_ingestion import AppendResearchStore, current_identity
from app.services.vnext_research_store import digest

CONTRACT = 'isolated-daily-research-bridge-v1'


def cold_packet(config, *, registration, as_of, source_generation, reference_owners=None):
    """Use the same canonical Composite/price/catalog builders as manual Primary."""
    code = registration['security']['ticker']
    store = AppendResearchStore(config)
    if current_identity(store, code) != registration:
        raise ValueError('daily_bridge_registration_drift')
    view = CompositeView(store, as_of=as_of, tickers=[code])
    if source_generation not in view.runs:
        raise ValueError('daily_bridge_generation_not_in_store')
    base = view.packet(code)
    base['public_security']['company_name'] = registration['security']['company_name']
    base['run_id'] = source_generation
    base = reduce_field_state(base)
    raw = dict(view.raw)
    base['price_attachment'] = build_price_attachment(base, raw)
    base['numeric_catalog'] = numeric_catalog(base) + numeric_price_catalog(base)
    return attach(base, **(reference_owners or {})), raw


class DailyResearchBridge:
    def __init__(self, *, registration, session, prior_session, as_of, plan_sha256,
                 recover_source, capture_source=None, prior_review=None,
                 primary=None, registry=None, reference_owners=None, recovery_source_config=None):
        if (not callable(recover_source) or capture_source is not None and not callable(capture_source)
                or prior_review is not None and not callable(prior_review)
                or primary is not None and not callable(primary)):
            raise ValueError('daily_bridge_backend_capabilities_required')
        if (len(plan_sha256) != 64 or any(c not in '0123456789abcdef' for c in plan_sha256)
                or date.fromisoformat(prior_session) >= date.fromisoformat(session)):
            raise ValueError('daily_bridge_plan_or_session')
        self.registration = deepcopy(registration)
        self.session, self.prior_session, self.as_of = session, prior_session, as_of
        self.recover_source, self.capture_source = recover_source, capture_source
        self.prior_review, self.primary = prior_review, primary
        self.reference_owners = dict(reference_owners or {})
        self.recovery_source_config = recovery_source_config
        if recovery_source_config is not None and (
                recovery_source_config.environment != 'test' or recovery_source_config.mode != 'read_only'):
            raise ValueError('daily_recovery_source_read_only_isolated_required')
        if set(self.reference_owners) - {'numeric_owner', 'historical_owner', 'technical_owner'}:
            raise ValueError('daily_bridge_original_reference_contract_only')
        self.registry = registry if registry is not None else UseRegistry()
        if not isinstance(self.registry, UseRegistry):
            raise ValueError('daily_bridge_live_use_registry_required')
        self.request = dict(contract=CONTRACT, registration=deepcopy(registration),
            session=session, prior_session=prior_session, as_of=as_of, plan_sha256=plan_sha256)
        self.key = digest(self.request)[:40]

    def status(self, controller):
        """Read-only observation, not accepted Owner/AI rehydration."""
        return dict(contract=CONTRACT, source_started=controller._read('bridge-start-'+self.key, self.request),
            source_captured=controller._read('bridge-captured-'+self.key, self.request),
            prior_terminal=controller._read('bridge-terminal-'+self.key, self.request),
            observation_only=True, authority_revalidated=False, send=False, scheduler=False)

    def _source(self, controller, *, allow_capture):
        started = controller._read('bridge-start-'+self.key, self.request)
        owner = self.recover_source()
        if owner is None:
            if started is not None:
                return None, 'CAPTURE_OUTCOME_UNKNOWN_NO_AUTOMATIC_RETRY'
            if not allow_capture or self.capture_source is None:
                return None, 'SOURCE_NOT_CHECKED'
            controller._append('bridge-start-'+self.key, self.request, dict(state='PREPARED'))
            owner = self.capture_source()
        if not isinstance(owner, DailyDeltaOwner):
            raise ValueError('daily_bridge_original_delta_owner_required')
        batch = owner.batch()
        code = self.registration['security']['ticker']
        if (batch['registrations'] != {code:self.registration}
                or self.as_of is not None and owner.as_of != self.as_of
                or any(o['payload']['calendar']['session'] != self.session for o in batch['observations'])):
            raise ValueError('daily_bridge_source_scope_binding')
        previous = [o['payload']['calendar']['session'] for o in owner.prior.batch()['observations']
            if o['ticker'] == code and o['field'] in ('completed_close', 'ohlcv.adjusted_daily')]
        if not previous or max(previous) != self.prior_session:
            raise ValueError('daily_bridge_prior_session_binding')
        controller._append('bridge-captured-'+self.key, self.request,
            dict(state='OWNER_CAPTURED', batch_sha256=digest(batch)))
        return owner, 'OWNER_CAPTURED'

    def _read_only_recovery_source(self, controller, owner):
        """Requalify original bytes in place; relocation changes snapshot identity.

        The new host store owns only recovery journals/outbox. An old source
        receipt alone is insufficient: the live Owner and cold parser both run.
        """
        store = AppendResearchStore(self.recovery_source_config)
        _persistent_registry(store, self.registry)
        batch = owner.batch()
        request = dict(contract=CONTROLLER_CONTRACT, batch=digest(batch), uses=self.registry.fingerprint())
        name = 'vnext-runtime-v1:job:daily-source-cold-'+digest(request)[:40]
        with store.connect() as c:
            row = c.execute('SELECT value FROM research_meta WHERE key=?',(name,)).fetchone()
        if row is None:
            raise ValueError('daily_recovery_original_source_journal_missing')
        record = json.loads(row[0])
        view = CompositeView(store, as_of=owner.as_of, tickers=list(batch['registrations']))
        packets = {code:view.packet(code) for code in batch['registrations']}
        if (record['status'] != 'COMMITTED' or record['request_sha256'] != digest(request) or
                record['result'] != dict(state='COLD_COMPOSITE_READY',packets={k:digest(v) for k,v in packets.items()}) or
                any(not any(e['record_id']==o['observation_id'] for e in packets[o['ticker']]['evidence'])
                    for o in batch['observations'])):
            raise ValueError('daily_recovery_original_source_binding')
        return dict(state='COLD_COMPOSITE_READY', result=dict(total_inserts=dict.fromkeys(_counts(store),0)))

    def execute(self, controller, *, allow_capture=False, allow_primary=False, fail_at=None,
                execution_authority=None, unified_review=None, unified_enabled=False):
        if not controller.enabled:
            return dict(contract=CONTRACT, state='DISABLED_DRY_RUN', send=False)
        if controller.config.environment != 'test' or controller.config.mode != 'write':
            raise ValueError('daily_bridge_isolated_only')
        if unified_enabled or unified_review is not None:
            if not unified_enabled or allow_primary:
                raise ValueError('unified_accepted_stages_only_no_legacy_primary')
            from app.services.vnext_balanced_stage_review import StageReviewOwner, UNIFIED, UNIFIED_AI_VERSIONS
            if (type(unified_review) is not StageReviewOwner or
                    unified_review.blind.version not in (UNIFIED, *UNIFIED_AI_VERSIONS) or
                    unified_review.adjudication.version != unified_review.blind.version):
                raise ValueError('unified_original_two_stage_owner_required')
        if execution_authority is not None:
            from app.services.vnext_daily_entrypoint import FreshDailyAuthority
            if type(execution_authority) is not FreshDailyAuthority:
                raise ValueError('daily_live_execution_authority_required')
            execution_authority.check(controller.config, self)
            if allow_capture != execution_authority.capture or allow_primary != execution_authority.primary:
                raise ValueError('daily_authority_permission_binding')
        read_only_reuse = self.prior_review is not None and not allow_capture and not allow_primary
        if self.recovery_source_config is not None and not read_only_reuse and (
                controller._host_initialization_recovery is None or allow_capture or not allow_primary):
            raise ValueError('daily_read_only_source_requires_host_recovery')
        before = _counts(controller.store)
        owner, source_state = self._source(controller, allow_capture=allow_capture)
        if owner is None:
            return dict(contract=CONTRACT, state=source_state, send=False, model_new=0)
        if fail_at == 'AFTER_CAPTURE':
            raise RuntimeError('injected_after_capture')
        source = (self._read_only_recovery_source(controller, owner) if self.recovery_source_config else
            controller.source(owner=owner, registry=self.registry,
                fail_at='AFTER_APPEND' if fail_at == 'AFTER_APPEND' else None))
        batch = owner.batch()
        packet, raw = cold_packet(self.recovery_source_config or controller.config, registration=self.registration,
            as_of=owner.as_of, source_generation=batch['runs'][0]['run_id'],
            reference_owners=self.reference_owners)
        _persistent_registry(controller.store, self.registry)
        if unified_enabled or unified_review is not None:
            # Opt-in dispatch replaces the legacy judgment/renderer, not source
            # capture. The cold builder above still runs and must match the
            # exact input accepted by the original two-stage controller.
            return self.consume_unified(controller,packet=packet,review=unified_review,enabled=unified_enabled)
        stages = stage_state(packet['base'], self.registration, self.registry)
        previous = self.prior_review() if self.prior_review else None
        bound = None
        if previous is not None:
            review_owner, prompts = previous
            bound = WholeVerdictDependencies(review_owner, registration=self.registration, prompts=prompts)
        dependency = bound.review(packet['base'], registry=self.registry, registration=self.registration) if bound else dict(
            status='PRIOR_RESULT_DEPENDENCY_UNVERIFIED', reusable=False)
        initial = stage_state(bound.base, self.registration, UseRegistry()) if bound else {}
        actions = stage_actions(initial, stages)
        parents = None
        if execution_authority is not None:
            parents = execution_authority.parents(controller.config, self, packet, stages)
            for name in parents['blocked_stages']:
                actions[name].update(action='STAGE_WAIT_SOURCE', reason='REQUIRED_CURRENT_PARENT_MISSING')
            if parents['blocked_stages']:
                dependency = dict(dependency, reusable=False, status='REQUIRED_CURRENT_PARENT_MISSING')
            elif previous is not None and (not execution_authority.prior_matches(previous) or
                    previous[0].dependency_record()['packet'] != packet):
                dependency = dict(dependency, reusable=False, status='FROZEN_WHOLE_CONTEXT_CHANGED')
        for action in actions.values():
            action.update(prior_verdict_reusable=dependency['reusable'], model_dependency_status=dependency['status'])
        checked = None
        accepted_record = None
        model_state = 'MODEL_DIRTY_NOT_ADMITTED'
        model_new = 0
        if dependency['reusable']:
            checked = bound.consume(packet['base'], registry=self.registry, registration=self.registration)
            accepted_record = review_owner.dependency_record()
            model_state = 'MODEL_REUSED'
        elif dependency['status'] == 'REVOKED_DEPENDENCY':
            model_state = 'MODEL_DIRTY_NOT_ADMITTED'
        elif any(v['source_eligible'] for v in stages.values()) and not (parents and parents['blocked_stages']):
            model_state = 'MODEL_PENDING_APPROVAL'
            if allow_primary and self.primary is not None:
                if execution_authority is not None:
                    execution_authority.check(controller.config, self)
                # The Primary capability must enforce its exact prompt approval,
                # signed-in transport, shared deadline and durable stage journal.
                produced = self.primary(controller, packet, raw, self.registration, self.session)
                if produced is not None:
                    new_owner, prompts, attempts = produced
                    if not isinstance(new_owner, ReviewOwner) or type(attempts) is not int or not 0 <= attempts <= 2:
                        raise ValueError('daily_bridge_primary_owner_required')
                    if new_owner.dependency_record()['packet'] != packet:
                        raise ValueError('daily_bridge_primary_packet_binding')
                    cycle = cycle_identity(registration=self.registration, session=self.session,
                        source_generation=packet['base']['run_id'], correction_epoch='',
                        canonical_input_digest=digest(packet))
                    controller.finalize(cycle=cycle, packet=packet, owner=new_owner,
                        registry=self.registry, registration=self.registration, prompts=prompts)
                    checked = new_owner.consume(new_owner.issue(), packet=packet)
                    accepted_record = new_owner.dependency_record()
                    model_new = attempts
                    model_state = 'MODEL_NEW_VALIDATED' if attempts else 'MODEL_REUSED'
        previous_terminal = controller._read('bridge-terminal-'+self.key, self.request)
        review_digest = digest(accepted_record) if accepted_record is not None else None
        review_key = 'bridge-review-' + digest([self.key, review_digest])[:40]
        review_event = controller._read(review_key, self.request) if review_digest else None
        if review_event and review_event['model_state'] == 'MODEL_NEW_VALIDATED':
            model_state = 'MODEL_NEW_VALIDATED'
        elif review_digest and review_event is None:
            controller._append(review_key, self.request,
                dict(review_sha256=review_digest, model_state=model_state))
        if (previous_terminal and review_digest and previous_terminal.get('review_sha256') == review_digest
                and previous_terminal['model_state'] == 'MODEL_NEW_VALIDATED'):
            model_state = 'MODEL_NEW_VALIDATED'
        if fail_at == 'BEFORE_MESSAGE':
            raise RuntimeError('injected_before_bridge_message')
        if checked is None:
            message = compact_message(self.registration['security']['ticker'], self.session,
                None, actions, audit_ref='Original source/whole-review Owner receipts')
        else:
            # Render the whole validated judgment, not independently signed stages.
            display = {k:dict(v, action='REUSE_VALID_PRIOR', prior_verdict_reusable=True)
                       for k,v in actions.items()}
            message = compact_message(self.registration['security']['ticker'], self.session,
                checked, display, audit_ref='Original source/whole-review Owner receipts',
                event_kind='ORIGINAL_NEW_SOURCE_AND_PRIMARY_GENERATION' if model_state == 'MODEL_NEW_VALIDATED'
                    else 'COLD_REUSE_SAME_DIGEST')
            value = checked['rendered']
            message += '\n\n' + value['entry_timing_view'] + '\n\n' + value['uncertainty']
            for role in ('economic_drivers_positive', 'economic_drivers_negative'):
                for row in value[role]:
                    message += '\n\n' + row['claim'] + '\n' + row['mechanism'] + '\n' + row['limitations']
            for role, keys in (('newbuyer', ('entry','breakout','resistance','chart_invalidation','current_price_rr','support_entry_rr')),
                               ('holder', ('support','risk_review','resistance','add_position'))):
                for key in keys:
                    if value[role][key].strip():message += '\n\n' + value[role][key]
            message += '\n\n' + value['thesis_invalidation']
        original_as_of = accepted_record['packet']['base']['as_of'] if accepted_record else None
        message += '\n\nMODEL_STATE=' + model_state
        message += '\nPRIOR_SIGNED_MODEL_AS_OF=' + str(original_as_of)
        message += '\nSOURCE_SESSION=' + self.session
        if parents is None:
            message += '; release/Market current discovery NOT_CHECKED.'
        if parents is not None:
            message += '\nCURRENT_MARKET=' + parents['parents']['market']['state']
            message += '; CURRENT_RELEASE=' + parents['parents']['release']['state']
            message += '; dated research only, not a current-market or no-new-filing conclusion.'
        message += '\nNO_SEND; VIRTUAL HOLDER; RESEARCH_ONLY; Strict READY not granted.\n'
        terminal = dict(state='MESSAGE_READY_NO_SEND', source='COLD_CONSUMED',
            source_batch_sha256=digest(batch), packet_sha256=digest(packet),
            model_state=model_state, review_sha256=review_digest,
            message_sha256=digest(message), send=False)
        # A later approved model may replace a pending overlay, never its bytes.
        version = digest([self.key, terminal])[:40]
        controller._append('bridge-message-'+version, self.request, terminal)
        if controller._read('bridge-terminal-'+self.key, self.request) is None:
            controller._append('bridge-terminal-'+self.key, self.request, terminal)
        after = _counts(controller.store)
        return dict(terminal, contract=CONTRACT, source_result=source['state'],
            source_delta_inserts=source['result']['total_inserts'],
            actual_inserts={k:after[k]-before[k] for k in before},
            stages=stages, actions=actions, model_dependency=dependency,
            model_new=model_new, model_reused=bool(checked and model_new == 0),
            model_output_scope='WHOLE_VERDICT', message=message,
            source_generation=batch['runs'][0]['run_id'], source_as_of=owner.as_of,
            prior_signed_model_as_of=original_as_of, market_owner='NOT_CHECKED',
            current_parent_review=parents,
            scheduler=False, strict_ready=False, private_holdings_used=False)

    def consume_unified(self, controller, *, packet, review, enabled=False):
        from app.services.vnext_balanced_stage_review import StageReviewOwner, UNIFIED, UNIFIED_AI_VERSIONS, output_contract
        from app.services.vnext_unified_judgment import build_bundle
        from app.vnext_worker import run_unified_no_send
        if not enabled:
            raise ValueError('unified_dispatch_default_off')
        if type(review) is not StageReviewOwner or review.blind.version not in (UNIFIED, *UNIFIED_AI_VERSIONS):
            raise ValueError('unified_original_two_stage_owner_required')
        timing_owner = review.blind.inputs.get('timing_owner')
        cutoff = review.blind.packet['technical']['technical']['cutoff'] if review.blind.packet['technical'] else None
        bundle = build_bundle(packet,registry=self.registry,timing_owner=timing_owner,cutoff=cutoff,
                              contract=output_contract(review.blind.version))
        if bundle['base']['public_security'] != self.registration['security']:
            raise ValueError('unified_daily_security_binding')
        context = dict(observed_as_of=self.as_of,completed_market_session=self.session,
            freshness_by_source={e['ref']:e['observed_at'] for e in bundle['admissibility']},
            required_market_fields={'state':'NOT_CHECKED'},current_price_denials=['CURRENT_PRICE_NOT_QUALIFIED'],
            source_revisions={e['ref']:e['source_sha'] for e in bundle['admissibility']})
        return run_unified_no_send(controller,packet=bundle,owner=review,mode='DAILY_NO_SEND',
                                   output_context=context,enabled=True)
