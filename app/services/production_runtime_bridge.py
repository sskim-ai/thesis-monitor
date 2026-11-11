"""Concrete runtime ports under qualification; live selection stays fail-closed.

SourceBackend must still be qualified against the complete canonical acquisition
DAG before this bridge can be registered by the production launcher.
"""
import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Protocol

from app.services.production_b2_execution import ModelTransportError, SemanticReject, authorize_b2, execute_b2
from app.services.production_message_renderer import market_message, stock_message
from app.services.production_monitoring_session import ProductionMonitoringSession
from app.services.fixture_context_authority import reject_test_only_production
from app.services.production_runtime_preflight import runtime_preflight
from app.services.production_source_execution import ProductionCollection, ProductionSnapshotPolicy, validate_production_collection
from app.services.unified_run_artifacts import durable_bytes, durable_json
from app.services.unified_runtime_v2 import CONTRACT, STAGES, StageResultV2, validate_stage_v2
from app.services.unified_snapshot_contract import digest
from app.services import new_buyer_base_contract as wire
from app.services.production_model_profile import sol_high
from app.services import new_buyer_request_owner as canonical_b2


class SourceBackend(Protocol):
    async def policy(self, market, session, run_id) -> ProductionSnapshotPolicy: ...
    async def collect(self, request, directory: Path) -> ProductionCollection: ...
    def verify(self, collection: ProductionCollection) -> dict: ...


class ProductionRuntimeBridgeV1:
    """Implements PipelinePorts without owning economic rules or implicit I/O."""

    def __init__(self, *, settings, sources: SourceBackend, model, delivery, clock,
                 authority_native_v2=False, native_owner_parents=None, execution_profile=None):
        self.execution_profile = sol_high(execution_profile) if execution_profile is not None else None
        if self.execution_profile is not None and getattr(model, 'execution_profile', None) != self.execution_profile:
            raise ValueError('production_bridge_transport_profile_mismatch')
        if type(authority_native_v2) is not bool:
            raise ValueError('explicit_native_bridge_gate_required')
        if not authority_native_v2 and native_owner_parents is not None:
            raise ValueError('native_parent_requires_explicit_bridge_gate')
        if authority_native_v2:
            from app.services.native_owner_session import BackendOwnerParent
            if not native_owner_parents or any(not isinstance(p, BackendOwnerParent) for p in native_owner_parents.values()):
                raise ValueError('backend_parent_capabilities_required')
        self._native_owner_parents = dict(native_owner_parents or {})
        self.settings, self.sources, self.model, self.delivery, self.clock = settings, sources, model, delivery, clock
        self.policies = {}

    async def policy(self, market, session, run_id):
        policy = await self.sources.policy(market, session, run_id)
        if not isinstance(policy, ProductionSnapshotPolicy):
            raise ValueError('production_source_policy_required')
        runtime_preflight(self.settings, policy)
        self.model.bind_cycle(market=market, run_id=run_id)
        self.policies[run_id] = policy
        return policy

    async def collect(self, request, directory):
        reject_test_only_production(request)
        policy = self.policies[request['run_id']]
        if request['contract'] != CONTRACT or request['policy_sha256'] != digest(policy.model_dump(mode='json')):
            raise ValueError('production_collect_policy_drift')
        runtime_preflight(self.settings, policy)
        result = await self.sources.collect(deepcopy(request), directory)
        if not isinstance(result, ProductionCollection):
            raise ValueError('production_source_envelope_required')
        return result

    async def _invoke(self, session, stage, request, directory):
        reject_test_only_production(request)
        if self._native_owner_parents:
            raise ValueError('offline_native_parent_requires_explicit_native_response_path')
        payload = deepcopy(request['payload'])
        profile = getattr(self, 'execution_profile', None)
        scope = {}
        budget = getattr(self.model, 'call_budget', None)
        dynamic = profile is not None and budget is not None and budget.plan is not None
        if profile:
            if dynamic:
                session.verify_model_build(stage, request)
                scope['slot_scope'] = budget.bind_stage(stage, request)
            else:
                subjects = request['subjects']
                if stage != 'MARKET' and len(subjects) != 1:
                    raise ValueError('sol_high_multi_subject_batch_outside_four_panel_plan')
                scope['panel'] = session.market.upper() + '_MARKET' if stage == 'MARKET' else subjects[0]
        for index in range(1, 2 if profile else 4):
            path = directory / ('attempt-'+str(index))
            receipt = dict(request_sha256=digest(payload), classification='INTENT', ordinal=index)
            durable_json(path/'intent.json', receipt, exclusive=True)
            try:
                raw = await asyncio.wait_for(self.model.request(deepcopy(payload),
                    model=profile.model if profile else 'gpt-5.6-sol',
                    effort=profile.effort if profile else 'xhigh', timeout=600, stage=stage, **scope), 600)
            except (ModelTransportError, TimeoutError) as exc:
                receipt.update(classification='TRANSPORT_FAILURE', error_type=type(exc).__name__)
            else:
                if not isinstance(raw, bytes):
                    raise TypeError('production_raw_response_required')
                durable_bytes(path/'response.raw', raw, exclusive=True)
                receipt['raw_sha256'] = hashlib.sha256(raw).hexdigest()
                try:
                    output = json.loads(raw)
                except (ValueError, UnicodeError):
                    receipt['classification'] = 'RESPONSE_FORM_FAILURE'
                else:
                    if wire.validate_json_schema(output, payload['response_schema']):
                        receipt['classification'] = 'PROVIDER_SCHEMA_FAILURE'
                    else:
                        try:
                            session.accept(stage, request, output)
                        except (ValueError, AssertionError) as exc:
                            receipt.update(classification='SEMANTIC_REJECT', error_type=type(exc).__name__)
                            durable_json(path/'receipt.json', receipt, exclusive=True)
                            raise SemanticReject('production_semantic_reject_no_retry') from exc
                        receipt['classification'] = 'ACCEPTED'
                        if dynamic:
                            budget.record_acceptance(scope['slot_scope']['slot_id'],
                                payload_sha256=digest(payload), output_sha256=receipt['raw_sha256'])
                        durable_json(path/'receipt.json', receipt, exclusive=True)
                        return dict(batch=request['batch'], subjects=list(request['subjects']), output=output,
                            payload_sha256=digest(payload), raw_sha256=receipt['raw_sha256'])
            durable_json(path/'receipt.json', receipt, exclusive=True)
        raise ModelTransportError('production_transport_form_budget_exhausted')

    def _session(self, request, directory):
        collection = ProductionCollection.model_validate(request['snapshot']['collection'])
        policy = self.policies[request['run_id']]
        errors = validate_production_collection(collection, policy=policy, run_id=request['run_id'],
            attempt_id=collection.attempt_id, started_at=collection.started_at, now=self.clock.now())
        if errors or digest(request['snapshot']) != request['snapshot_sha256']:
            raise ValueError('production_source_revalidation_failed')
        self.sources.verify(collection)
        source = collection.packet['monitoring_input']
        native_args = {}
        budget = getattr(self.model, 'call_budget', None)
        if budget is not None and budget.plan is not None:
            native_args.update(frozen_cohort=budget.plan.cohort,
                              cohort_source_owner=self.model.cohort_source_owner)
        if self._native_owner_parents:
            parent = self._native_owner_parents.get(request['run_id'])
            if parent is None:
                raise ValueError('native_parent_run_missing_no_legacy_fallback')
            scope = dict(run_id=request['run_id'], market=collection.market,
                generation_id=collection.production_envelope.generation_id,
                source_generation_id=source['source_generation_id'], snapshot_sha256=request['snapshot_sha256'])
            parent.verify_scope(**scope)
            native_args.update(authority_native_v2=True, native_owner_parent=parent, native_parent_scope=scope)
        session = ProductionMonitoringSession(directory/'canonical', market=collection.market,
            generation_id=collection.production_envelope.generation_id, source=source,
            source_generation_id=source['source_generation_id'], **native_args)
        self._restore_upstream(session, request)
        return session, collection

    def _restore_upstream(self, session, request):
        for stage in STAGES[:STAGES.index(request['stage'])]:
            if stage not in {'MARKET', 'CORE', 'A', 'B'}:
                continue
            rows = request['inputs'][stage]['output']['rows']
            captured = session.build(stage)
            if len(rows) != len(captured):
                raise ValueError('production_upstream_batch_coverage')
            for item, row in zip(captured, rows, strict=True):
                if (row['batch'] != item['batch'] or row['subjects'] != list(item['subjects'])
                        or row['payload_sha256'] != digest(item['payload'])):
                    raise ValueError('production_upstream_payload_drift')
                session.accept(stage, item, row['output'])

    async def stage(self, request, directory):
        reject_test_only_production(request)
        if self.execution_profile is not None and request['stage'] == 'DELIVER':
            raise ValueError('sol_high_no_send_delivery_forbidden')
        if self._native_owner_parents:
            raise ValueError('offline_native_parent_not_canonical_batch_migration')
        if request['contract'] != CONTRACT:
            raise ValueError('production_runtime_v2_required')
        probe = StageResultV2(run_id=request['run_id'], generation_id=request['snapshot']['collection']['production_envelope']['generation_id'],
            snapshot_sha256=request['snapshot_sha256'], request_sha256=digest(request), stage=request['stage'], status='PASS', output={})
        validate_stage_v2(probe, request)
        session, collection = self._session(request, directory)
        stage = request['stage']
        if stage in {'MARKET', 'CORE', 'A', 'B'}:
            rows = []
            for item in session.build(stage):
                rows.append(await self._invoke(session, stage, item, directory/('model-'+str(item['batch']))))
            output = dict(rows=rows, generation_id=session.gen)
        elif stage == 'B2':
            rows = {}
            for ticker in collection.production_envelope.subjects:
                item = session.b2_request(ticker)
                reject_test_only_production(item)
                binding = dict(generation_id=session.gen, source_generation_id=session.source_gen,
                    source_envelope_sha256=digest(collection.production_envelope.model_dump(mode='json')),
                    owner_sha256=digest(session.fresh_stocks[ticker]), core_sha256=digest(session.cores[ticker]),
                    pass_a_sha256=digest(session.arows[ticker]), pass_b_sha256=digest(session.brows[ticker]))
                auth = authorize_b2(item, **binding, execution_profile=self.execution_profile)
                budget = getattr(self.model, 'call_budget', None)
                b2_scope = None
                if budget is not None and budget.plan is not None:
                    payload = canonical_b2.provider_payload(item, expected_request_sha256=auth.request_sha256)
                    b2_scope = budget.bind_stage('B2', dict(market=session.market, batch=None, subjects=[ticker],
                        execution_generation_id=session.gen, source_generation_id=session.source_gen,
                        payload=payload, payload_sha256=auth.request_sha256,
                        original_authorization_sha256=digest(auth.model_dump(mode='json'))))
                result = await execute_b2(item, auth, current_binding=binding, transport=self.model, directory=directory/ticker)
                if b2_scope is not None:
                    budget.record_acceptance(b2_scope['slot_id'], payload_sha256=auth.request_sha256,
                                             output_sha256=result['attempts'][-1]['raw_sha256'])
                rows[ticker] = dict(authorization=auth.model_dump(mode='json'), result=result)
            output = dict(rows=rows, generation_id=session.gen)
        else:
            b2_rows = request['inputs']['B2']['output']['rows']
            if set(b2_rows) != set(collection.production_envelope.subjects):
                raise ValueError('production_b2_complete_current_cohort_required')
            if stage in {'VALIDATE', 'RENDER'}:
                scope = dict(execution_profile=self.execution_profile) if self.execution_profile else {}
                messages = [market_message(session)] + [stock_message(session, t, b2_rows[t], **scope) for t in collection.production_envelope.subjects]
                for message in messages:
                    message['snapshot_sha256'] = request['snapshot_sha256']
                    if self.execution_profile:
                        message['NO_SEND'] = True
                output = dict(messages=messages, generation_id=session.gen, finality_claim='NOT_CLAIMED') if stage == 'RENDER' else dict(
                    status='PASS', message_count=len(messages), content_sha256=digest(messages), generation_id=session.gen)
            else:
                messages = request['inputs']['RENDER']['output']['messages']
                if digest(messages) != request['inputs']['VALIDATE']['output']['content_sha256']:
                    raise ValueError('production_render_content_changed')
                output = await self.delivery.deliver(run_id=request['run_id'], generation_id=session.gen, messages=messages)
        result = probe.model_copy(update={'output': output})
        validate_stage_v2(result, request)
        return result

    async def notify_failure(self, payload):
        if self.execution_profile is not None:
            raise ValueError('sol_high_no_send_delivery_forbidden')
        message = dict(message_id='OPERATIONAL_FAILURE', generation_id=payload['run_id'],
            text='[MONITORING OPERATIONAL FAILURE]\n'+json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return await self.delivery.deliver(run_id=payload['run_id'], generation_id=payload['run_id'], messages=[message])
