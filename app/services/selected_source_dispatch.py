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
                 approved_plan_sha256, approved_provider_caps, guard, secrets=(), enabled=False):
        if enabled is not True:
            raise ValueError('selected_source_dispatch_default_off')
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
        final=await super().execute(*args,**kwargs)
        if any(a['status']==429 or a.get('error') for a in final['attempts']):
            self.halted=True
            raise SourceSafetyStop('selected_quota_or_uncertain_transport_stop')
        return final
