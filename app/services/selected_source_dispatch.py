"""Opt-in selected source admission over the original sealed wire executor.

This does not install/qualify a host, create user consent, or confer financial
use. Original Worker, account STOP/Lane, parsers and economic owners still apply.
"""
from pathlib import Path
import re

from app.services.sealed_fresh_dispatch import SealedDispatcher
from app.services.sealed_response_binding import binding_owner_hash
from app.services.selected_source_plan import SelectedRequestPlan, compile_selected_plan, request_budget
from app.services.selected_source_registration import local_seed
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_live_source_transport import SourceSafetyStop


def optional_night_scope(plan, descriptor):
    if (plan.contract != 'selected-original-source-request-plan-v1' or plan.market != 'us'
            or descriptor.provider != 'krx_night_futures' or descriptor.market != 'kr'
            or descriptor.subject != 'KOSPI200' or descriptor.mandatory
            or descriptor.endpoint_operation != 'fut_bydd_trd' or descriptor.response_binding
            or descriptor.transient_retry_max != 0 or descriptor.timeout_seconds > 20
            or descriptor.consumer_role != descriptor.logical_request_id
            or re.fullmatch(r'night:KOSPI200:\d{4}-\d{2}-\d{2}', descriptor.logical_request_id) is None):
        return None
    return dict(logical_id=descriptor.logical_request_id, mandatory=False, operation='fut_bydd_trd',
        plan_sha256=plan.plan_sha256, descriptor_sha256=descriptor.descriptor_sha256)


def _night_attempt(cap, scope, identity):
    from app.services.campaign_runtime_cap import optional_night_result
    matches = [key for key, attempt in cap.state()['attempts'].items()
        if attempt.get('optional_night') == scope and optional_night_result(attempt, identity)]
    if len(matches) > 1:
        raise SourceSafetyStop('selected_optional_night_physical_result_ambiguous')
    return matches[0] if matches else None


def _dart_unavailable(cap, logical, identity):
    from app.services.campaign_runtime_cap import optional_dart_result
    for key, attempt in cap.state()['attempts'].items():
        if attempt.get('optional_dart') == logical and optional_dart_result(attempt, identity):
            return key
    return None


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
        if self.plan.market=='us' and 'SKHY' in self.plan.subjects:
            from app.services.selected_source_plan import require_issuer_descriptors
            require_issuer_descriptors(self.plan,rebuilt['candidate'])
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
        state = run_ledger.state()
        if (state['plans'].get(self.plan.market) != self.plan.plan_sha256
                or run_ledger.identity.get('plan_http_market') and
                state['runtime']['http_budget']['providers'] != approved_provider_caps):
            raise ValueError('selected_shared_run_plan_not_bound')
        self._require_current()
        self._qualified_registration = (registration_owner, stock, policy)
        self.admission = dict(contract='selected-original-source-admission-v1',
            live_dispatch_allowed=True,plan_sha256=self.plan.plan_sha256,
            generation_id=self.plan.generation_id,historical_receipt_dependency=False,
            financial_use_granted=False,approved_provider_caps=approved_provider_caps)
        self._initialize(root=root,secrets=secrets)

    def _require_current(self):
        self.guard()
        qualified = getattr(self, '_qualified_registration', None)
        if qualified is None:
            local_seed(self.registration_owner, stock=self.stock, policy=self.policy)
            return
        if any(current is not original for current, original in zip(
                (self.registration_owner, self.stock, self.policy), qualified, strict=True)):
            raise SourceSafetyStop('selected_registration_scope_changed')
        # Rebuilding the unchanged Class-C projection recreates memory DBs.
        # The original live Owner still checks expiry, revoke, code and policy.
        from app.services import prospective_class_c_owner as registration
        registration.require_generation(self.registration_owner, self.stock.run_id,
            purpose=registration.ROUTINE_SCOPE if self.stock.routine_us_no_send_source_seconds is not None else registration.SCOPE)

    async def execute(self,*args,**kwargs):
        self._require_current()
        ledger = getattr(self, 'run_ledger', None)
        if ledger is not None:
            parent, wire = self, kwargs['transport']
            logical = args[0] if args else kwargs['logical_id']
            descriptor = next(d for d in self.plan.descriptors if d.logical_request_id == logical)
            from app.services.campaign_runtime_cap import OPTIONAL_NEWS_429, OPTIONAL_NIGHT
            from app.services.selected_news_rate_limit import optional_scope
            optional = (optional_scope(self.plan, descriptor) if
                ledger.identity.get('runtime_cap', {}).get('optional_news_429') == OPTIONAL_NEWS_429 else None)
            optional_night = (optional_night_scope(self.plan, descriptor) if
                ledger.identity.get('runtime_cap', {}).get('optional_night') == OPTIONAL_NIGHT else None)
            dart_report = bool(ledger.identity.get('plan_http_market') == 'kr' and not descriptor.mandatory
                and descriptor.endpoint_operation == 'dart_report' and descriptor.response_binding
                and descriptor.response_binding.kind == 'DART_REPORT')
            report_unavailable = None
            class CountedTransport:
                optional_night_timeout = optional_night is not None
                optional_dart_timeout = dart_report

                async def handle_async_request(self, request):
                    nonlocal report_unavailable
                    parent._require_current()
                    key = parent.run_ledger.before_http(market=parent.plan.market, provider=descriptor.provider,
                        logical_id=logical, plan_sha256=parent.plan.plan_sha256)
                    metered = None
                    try:
                        if parent.run_ledger.identity.get('runtime_cap'):
                            from app.services.campaign_runtime_cap import MeteredAsyncTransport, CampaignOhlcvTransport
                            if descriptor.provider=='ohlcv_analyst':
                                metered=CampaignOhlcvTransport(binding=parent.run_ledger.worker_binding(),
                                    market=parent.plan.market,subject=descriptor.subject,phase='SOURCE',inner=wire)
                            else:
                                issuer_only=(parent.plan.market=='us' and descriptor.subject=='000660'
                                    and descriptor.provider=='opendart' and descriptor.consumer_role=='financial:000660')
                                metered=MeteredAsyncTransport(binding=parent.run_ledger.worker_binding(),
                                    market=parent.plan.market,phase='SOURCE',owner='SelectedSourceDispatcher',inner=wire,
                                    **({'subject':descriptor.subject, 'optional_news':optional} if optional else
                                       {'optional_night':optional_night} if optional_night else
                                       {'subject':descriptor.subject} if dart_report else
                                       {'subject':'000660'} if issuer_only else {}))
                            if descriptor.endpoint_operation=='usa20590':
                                response=await _completed_close_on_lane(metered,request)
                            else:
                                response=await metered.handle_async_request(request)
                        else:
                            response = await wire.handle_async_request(request)
                    except BaseException:
                        unavailable = (_night_attempt(metered.cap, optional_night, ledger.identity)
                            if optional_night and metered is not None else None)
                        if dart_report and metered is not None:
                            report_unavailable = unavailable = _dart_unavailable(metered.cap, logical, ledger.identity)
                        parent.run_ledger.result(key, ok=False,
                            **({'optional_unavailable':unavailable} if unavailable else {}))
                        raise
                    optional_attempt = None
                    if optional and response.status_code == 429:
                        from app.services.campaign_runtime_cap import optional_news_result
                        matches = [k for k, a in metered.cap.state()['attempts'].items()
                            if a.get('optional_news') == optional and optional_news_result(a, ledger.identity)]
                        if len(matches) != 1:
                            raise SourceSafetyStop('selected_optional_news_physical_result_missing')
                        optional_attempt = matches[0]
                    if optional_night:
                        optional_attempt = _night_attempt(metered.cap, optional_night, ledger.identity)
                    if dart_report and response.status_code in (404, 410):
                        report_unavailable = optional_attempt = _dart_unavailable(metered.cap, logical, ledger.identity)
                        if optional_attempt is None:
                            raise SourceSafetyStop('selected_optional_dart_physical_result_missing')
                    parent.run_ledger.result(key, ok=False if optional_attempt else response.status_code not in (401,403,429),
                        **({'optional_unavailable':optional_attempt} if optional_attempt else {}))
                    return response
            kwargs['transport'] = CountedTransport()
        try:
            final=await super().execute(*args,**kwargs)
        except BaseException:
            if ledger is not None:
                ledger.stop('SOURCE_DISPATCH_FAILED')
            raise
        optional_429 = (ledger is not None and optional and final['status'] == 'FAILED'
            and len(final['attempts']) == 1 and final['attempts'][0]['status'] == 429
            and final['attempts'][0].get('error') is None)
        if ledger is not None and dart_report and final['status'] == 'FAILED':
            if report_unavailable:
                return final
            if any((a['status'] or 0) >= 400 or a.get('error') for a in final['attempts']):
                self.halted = True
                ledger.stop('SOURCE_DART_PROVIDER_FAILED')
                raise SourceSafetyStop('selected_dart_provider_failed')
        if ledger is not None and optional_night and final['status'] == 'FAILED':
            from app.services.campaign_runtime_cap import RuntimeCap, OptionalNightCollectionError
            attempt = _night_attempt(RuntimeCap(ledger.worker_binding()), optional_night, ledger.identity)
            if attempt is not None:
                # The original final and physical/logical failure receipts exist.
                # End the native lookback immediately so it cannot refetch this
                # provider or turn its stopped-provider latch into a global stop.
                raise OptionalNightCollectionError(logical, attempt)
        if not optional_429 and any(a['status']==429 or a.get('error') for a in final['attempts']):
            self.halted=True
            if ledger is not None:
                ledger.stop('SOURCE_QUOTA_OR_TRANSPORT_FAILED')
            raise SourceSafetyStop('selected_quota_or_uncertain_transport_stop')
        if ledger is not None and descriptor.mandatory and final['status']!='PASS':
            ledger.stop('MANDATORY_SOURCE_REJECTED')
            raise SourceSafetyStop('selected_mandatory_source_rejected')
        return final


async def _completed_close_on_lane(transport, request):
    # The native OHLCV worker already holds the host lane for its RPC.
    # usa20590 comes directly from the parent, so it needs the lane here.
    from app.services.kiwoom_global_lane import configured_lane, validate_envelope

    lane = configured_lane()
    if lane is None:
        raise SourceSafetyStop('selected_completed_close_original_lane_required')
    async with lane.slot():
        response = await transport.handle_async_request(request)
        response.request = request  # Direct transports do not attach the client request.
        validate_envelope(response)
        return response
