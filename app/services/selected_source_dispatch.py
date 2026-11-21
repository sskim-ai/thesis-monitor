"""Opt-in selected source admission over the original sealed wire executor.

This does not install/qualify a host, create user consent, or confer financial
use. Original Worker, account STOP/Lane, parsers and economic owners still apply.
"""
from pathlib import Path

from app.services.sealed_fresh_dispatch import SealedDispatcher
from app.services.sealed_response_binding import binding_owner_hash
from app.services.selected_source_plan import SelectedRequestPlan, compile_selected_plan, request_budget
from app.services.selected_source_registration import local_seed
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_live_source_transport import SourceSafetyStop


class SelectedSourceDispatcher(SealedDispatcher):
    def __init__(self, *, plan, compiler_args, kis_plan, registration_owner, policy,
                 config_identities, credential_presence, repository_root, root,
                 approved_plan_sha256, approved_provider_caps, guard, secrets=(), enabled=False, run_ledger=None):
        if enabled is not True:
            raise ValueError('selected_source_dispatch_default_off')
        if run_ledger is None:
            raise ValueError('selected_one_campaign_ledger_required')
        self.plan = SelectedRequestPlan.model_validate(plan)
        rebuilt = compile_selected_plan(compiler_args=compiler_args,kis_plan=kis_plan)
        stock = compiler_args['stock']
        if (stock.planning_only or rebuilt['plan']!=self.plan
                or approved_plan_sha256!=self.plan.plan_sha256
                or approved_provider_caps!=request_budget(rebuilt,kis_plan)['providers']):
            raise ValueError('selected_current_exact_plan_approval_required')
        if (self.plan.binding_owner_sha256!=binding_owner_hash()
                or not callable(guard)):
            raise ValueError('selected_original_binding_and_host_guard_required')
        base = Path(repository_root).resolve()
        for name, expected in rebuilt['owners'].items():
            p = base/name
            if (p.is_symlink() or not p.resolve().is_relative_to(base)
                    or sha256_bytes(p.read_bytes())!=expected):
                raise ValueError('selected_normalizer_owner_drift')
        for d in self.plan.descriptors:
            if (config_identities.get(d.provider)!=d.config_identity_sha256
                    or credential_presence.get(d.provider) is not True):
                raise ValueError('selected_original_provider_configuration_required')
        if kis_plan is not None and credential_presence.get('kis') is not True:
            raise ValueError('selected_kis_credentials_required')
        self.registration_owner,self.stock,self.policy,self.guard=registration_owner,stock,policy,guard
        self.run_ledger = run_ledger
        if run_ledger is not None and run_ledger.state()['plans'].get(self.plan.market) != self.plan.plan_sha256:
            raise ValueError('selected_shared_run_plan_not_bound')
        self._require_current()
        self.admission = dict(contract='selected-original-source-admission-v1',
            live_dispatch_allowed=True,plan_sha256=self.plan.plan_sha256,
            generation_id=self.plan.generation_id,historical_receipt_dependency=False,
            financial_use_granted=False,approved_provider_caps=approved_provider_caps)
        self._initialize(root=root,secrets=secrets)

    def _require_current(self):
        self.guard()
        local_seed(self.registration_owner,stock=self.stock,policy=self.policy)

    async def execute(self,*args,**kwargs):
        self._require_current()
        ledger = getattr(self, 'run_ledger', None)
        if ledger is not None:
            parent, wire = self, kwargs['transport']
            logical = args[0] if args else kwargs['logical_id']
            descriptor = next(d for d in self.plan.descriptors if d.logical_request_id == logical)
            class CountedTransport:
                async def handle_async_request(self, request):
                    parent._require_current()
                    key = parent.run_ledger.before_http(market=parent.plan.market, provider=descriptor.provider,
                        logical_id=logical, plan_sha256=parent.plan.plan_sha256)
                    try:
                        if parent.run_ledger.identity.get('runtime_cap'):
                            from app.services.campaign_runtime_cap import MeteredAsyncTransport, CampaignOhlcvTransport
                            if descriptor.provider=='ohlcv_analyst':
                                metered=CampaignOhlcvTransport(binding=parent.run_ledger.worker_binding(),
                                    market=parent.plan.market,subject=descriptor.subject,phase='SOURCE',inner=wire)
                            else:
                                metered=MeteredAsyncTransport(binding=parent.run_ledger.worker_binding(),
                                    market=parent.plan.market,phase='SOURCE',owner='SelectedSourceDispatcher',inner=wire)
                            response=await metered.handle_async_request(request)
                        else:
                            response = await wire.handle_async_request(request)
                    except BaseException:
                        parent.run_ledger.result(key, ok=False)
                        raise
                    parent.run_ledger.result(key, ok=response.status_code not in (401,403,429))
                    return response
            kwargs['transport'] = CountedTransport()
        try:
            final=await super().execute(*args,**kwargs)
        except BaseException:
            if ledger is not None:
                ledger.stop('SOURCE_DISPATCH_FAILED')
            raise
        if any(a['status']==429 or a.get('error') for a in final['attempts']):
            self.halted=True
            if ledger is not None:
                ledger.stop('SOURCE_QUOTA_OR_TRANSPORT_FAILED')
            raise SourceSafetyStop('selected_quota_or_uncertain_transport_stop')
        if ledger is not None and descriptor.mandatory and final['status']!='PASS':
            ledger.stop('MANDATORY_SOURCE_REJECTED')
            raise SourceSafetyStop('selected_mandatory_source_rejected')
        return final
