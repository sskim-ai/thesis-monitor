"""Process-local scoped dispatch; original execution/receipt semantics are reused.

Only a live original current-source parent grants dispatch. A versioned public
plan remains replay data, never authority to reconstruct that parent. One parent
gets one dispatcher lifetime; stopping or losing it does not replenish budget.
"""
from collections import Counter
import json
import zlib
from threading import RLock
from typing import Literal
from weakref import WeakKeyDictionary

import httpx
from pydantic import Field, model_validator

from app.services import source_dispatch_authority as parent_owner
from app.services.sealed_fresh_dispatch import (
    RequestPlan, SealedDispatcher, binding_owner_hash, stamp, wire_identity,
)
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_snapshot_contract import digest

CONTRACT = "current-scoped-source-request-plan-v1"
_LOCK = RLock()
_CLAIMED_PARENTS = WeakKeyDictionary()
_EXTRA_FIELDS = {"contract", "parent_receipt_sha256"}
_STOP_STATUSES = {401, 403, 429}
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
_ROUTES = {
    "ka10099": ("/api/dostk/stkinfo", {"mrkt_tp"}),
    "ka10001": ("/api/dostk/stkinfo", {"stk_cd"}),
    "usa06012": ("/api/us/chart", {"stex_tp", "stk_cd", "strt_dt", "upd_stkpc_tp", "exrt_appl_tp"}),
    "usa06013": ("/api/us/chart", {"stex_tp", "stk_cd", "strt_dt", "upd_stkpc_tp", "exrt_appl_tp"}),
    "usa06014": ("/api/us/chart", {"stex_tp", "stk_cd", "strt_dt", "upd_stkpc_tp", "exrt_appl_tp"}),
    "ka10081": ("/api/dostk/chart", {"stk_cd", "base_dt", "upd_stkpc_tp"}),
    "ka10082": ("/api/dostk/chart", {"stk_cd", "base_dt", "upd_stkpc_tp"}),
    "ka10083": ("/api/dostk/chart", {"stk_cd", "base_dt", "upd_stkpc_tp"}),
    "usa20590": ("/api/us/mrkcond", {"stex_tp", "stk_cd", "base_dt"}),
    "usa10099": ("/api/us/stkinfo", {"stex_tp"}),
    "ka20001": ("/api/dostk/sect", {"mrkt_tp", "inds_cd"}),
    "ka20003": ("/api/dostk/sect", {"inds_cd"}),
    "ka20009": ("/api/dostk/sect", {"mrkt_tp", "inds_cd"}),
    "ka10051": ("/api/dostk/sect", {"mrkt_tp", "amt_qty_tp", "base_dt", "stex_tp"}),
    "ka10066": ("/api/dostk/mrkcond", {"mrkt_tp", "amt_qty_tp", "trde_tp", "stex_tp"}),
    "credential_exchange": ("/oauth2/token", {"grant_type", "appkey", "secretkey"}),
}


def _readonly_wire(wire, operation):
    url = httpx.URL(wire["url"])
    route = _ROUTES.get(operation)
    body = json.loads(wire["body"])
    headers = dict(wire["headers"])
    if (route is None or wire["method"] != "POST"
            or url.scheme != "https" or url.host != "api.kiwoom.com"
            or url.port not in {None, 443} or url.userinfo or url.query or url.fragment
            or url.path != route[0] or not isinstance(body, dict)
            or set(body) != route[1] or not all(isinstance(v, str) for v in body.values())):
        raise ValueError("scoped_exact_kiwoom_read_route_required")
    if operation == "credential_exchange":
        if body["grant_type"] != "client_credentials" or headers.get("api-id"):
            raise ValueError("scoped_credential_exchange_shape")
    elif headers.get("api-id") != operation:
        raise ValueError("scoped_api_identity_mismatch")


class CurrentScopedRequestPlan(RequestPlan):
    contract: Literal["current-scoped-source-request-plan-v1"] = CONTRACT
    parent_receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    def original_plan(self):
        return RequestPlan.model_validate(self.model_dump(mode="json", exclude=_EXTRA_FIELDS))

    @model_validator(mode="after")
    def scoped_readonly(self):
        if self.unresolved_roles or not self.descriptors:
            raise ValueError("scoped_complete_frozen_plan_required")
        for descriptor in self.descriptors:
            if descriptor.provider != "kiwoom" or descriptor.transient_retry_max != 0:
                raise ValueError("scoped_kiwoom_only_no_retries")
            _readonly_wire(json.loads(descriptor.request_json), descriptor.endpoint_operation)
        return self


class _PhysicalKiwoomTransport(httpx.AsyncBaseTransport):
    def __init__(self, dispatcher, inner):
        self.dispatcher, self.inner = dispatcher, inner

    async def handle_async_request(self, request):
        pacer = self.dispatcher._account_pacer
        # This is inside original dispatch, immediately before physical I/O.
        # The optional policy only narrows this explicit scoped route.
        if pacer is not None:
            if self.dispatcher._pacing_context is not None:
                raise SourceSafetyStop('scoped_paced_retry_denied')
            context = pacer.slot()
            pacing = await context.__aenter__()
            self.dispatcher._pacing_context = context, pacing
            return await self._receive(request, pacing=pacing)
        return await self._receive(request)

    async def _receive(self, request, pacing=None):
        run = self.dispatcher
        with _LOCK:
            descriptor = run._authorize_physical(request)
            if run.physical_attempts >= run.maximum_attempts:
                run.halted = True
                raise SourceSafetyStop("scoped_physical_budget_exhausted")
            run.physical_attempts += 1
            category = run._category(descriptor)
            run._counts[category] += 1
            ordinal = run.physical_attempts
            receipt = dict(ordinal=ordinal, logical_request_id=descriptor.logical_request_id,
                generation_id=run.plan.generation_id, plan_sha256=run.plan.plan_sha256,
                category=category, operation=descriptor.endpoint_operation,
                started_at=stamp(), counter_before_io=True)
            if pacing is not None:
                receipt['account_pacing'] = dict(pacing)
            run._save(f"physical/attempt-{ordinal:04d}.start.json", receipt)
        try:
            # The original transport owns TLS verification; no redirect or TLS
            # settings are changed at this boundary.
            response = await self.inner.handle_async_request(request)
            receipt["http_status"] = response.status_code
            if response.status_code in _STOP_STATUSES:
                run.halted = True
                run._http_stop = response.status_code
            try:
                body = await _bounded_body(response, receipt)
                run._require_parent()
                headers = [(k, v) for k, v in response.headers.multi_items()
                           if k.lower() not in {"content-encoding", "content-length"}]
                return httpx.Response(response.status_code, content=body, headers=headers,
                                      request=request)
            finally:
                await response.aclose()
        except BaseException as exc:
            receipt["error_class"] = type(exc).__name__
            raise
        finally:
            receipt["finished_at"] = stamp()
            run._save(f"physical/attempt-{ordinal:04d}.json", receipt)


async def _bounded_body(response, receipt):
    """Bound wire and decoded bytes before the original dispatcher calls aread.

    Preloaded responses support MockTransport fixtures; real HTTPTransport uses
    the bounded raw stream. Bounded decompression prevents compressed expansion
    from allocating an unbounded decoded response before the size check.
    """
    receipt.update(response_limit_bytes=MAX_RESPONSE_BYTES, wire_bytes=0, decoded_bytes=0)
    if response.is_stream_consumed:
        body = response.content
        receipt.update(decoded_bytes=len(body), wire_bytes=None)
        if len(body) > MAX_RESPONSE_BYTES:
            raise SourceSafetyStop("scoped_response_body_limit")
        return body
    encoding = response.headers.get("content-encoding", "identity").strip().lower()
    if encoding not in {"", "identity", "gzip", "deflate"}:
        raise SourceSafetyStop("scoped_response_encoding_not_bounded")
    decoder = (zlib.decompressobj(16 + zlib.MAX_WBITS) if encoding == "gzip"
               else zlib.decompressobj() if encoding == "deflate" else None)
    chunks = []
    async for chunk in response.aiter_raw():
        receipt["wire_bytes"] += len(chunk)
        if receipt["wire_bytes"] > MAX_RESPONSE_BYTES:
            raise SourceSafetyStop("scoped_response_wire_limit")
        try:
            decoded = (decoder.decompress(chunk, MAX_RESPONSE_BYTES - receipt["decoded_bytes"] + 1)
                       if decoder else chunk)
        except zlib.error as exc:
            raise SourceSafetyStop("scoped_response_compression_invalid") from exc
        receipt["decoded_bytes"] += len(decoded)
        if receipt["decoded_bytes"] > MAX_RESPONSE_BYTES or (decoder and decoder.unconsumed_tail):
            raise SourceSafetyStop("scoped_response_body_limit")
        chunks.append(decoded)
    if decoder and (not decoder.eof or decoder.unused_data):
        raise SourceSafetyStop("scoped_response_compression_incomplete_or_trailing")
    return b"".join(chunks)


class CurrentScopedDispatcher(SealedDispatcher):
    credential_body_hash_evidence = False

    def __init__(self, *, parent, plan, root, owners, config_identities,
                 credential_presence, secrets=(), account_pacer=None):
        from app.services.kiwoom_global_lane import GlobalKiwoomLane, configured_lane
        host_lane = configured_lane()
        if host_lane is not None:
            if account_pacer is not None and account_pacer is not host_lane:
                raise ValueError('scoped_global_lane_override_denied')
            account_pacer = host_lane
        if account_pacer is not None:
            from app.services.kiwoom_account_pacing import AccountQueryPacer
            if type(account_pacer) not in {AccountQueryPacer, GlobalKiwoomLane}:
                raise ValueError('scoped_original_account_pacer_required')
        self._account_pacer = account_pacer
        self._pacing_context = None
        if isinstance(plan, CurrentScopedRequestPlan) or (
                isinstance(plan, dict) and plan.get("contract") == CONTRACT):
            candidate = CurrentScopedRequestPlan.model_validate(plan)
            original = candidate.original_plan()
        else:
            original = RequestPlan.model_validate(plan)
            candidate = None
        receipt = parent_owner.resolve_parent(parent, plan=original)
        public = CurrentScopedRequestPlan(**original.model_dump(mode="json"),
            parent_receipt_sha256=digest(receipt))
        if candidate is not None and candidate != public:
            raise ValueError("scoped_parent_receipt_binding_mismatch")
        maximum = receipt["maximum_attempts"]
        planned = sum(d.max_transport_attempts for d in public.descriptors)
        if (type(maximum) is not int or maximum < 1 or planned > maximum
                or receipt["planned_attempts"] != planned):
            raise ValueError("scoped_trusted_parent_budget_mismatch")
        if (public.binding_owner_sha256 is not None
                and public.binding_owner_sha256 != binding_owner_hash()):
            raise ValueError("scoped_response_binding_owner_drift")
        covered = {d.consumer_role for d in public.descriptors if d.mandatory}
        if not set(public.mandatory_roles) <= covered:
            raise ValueError("scoped_mandatory_role_missing")
        for descriptor in public.descriptors:
            parent_owner.authorize_descriptor(parent, descriptor, plan=original)
            if (owners.get(descriptor.normalizer) != descriptor.owner_sha256
                    or config_identities.get(descriptor.provider) != descriptor.config_identity_sha256
                    or credential_presence.get(descriptor.provider) is not True):
                raise ValueError("scoped_owner_config_or_credential_binding")
        self._parent, self._original = parent, original
        self.plan = public
        self.maximum_attempts = maximum
        self.physical_attempts = 0
        self._counts = Counter()
        self._active = None
        self._busy = False
        self._http_stop = None
        self.role_quality_denials = {}
        self.admission = dict(status="CURRENT_SCOPED_DISPATCH_ADMITTED_SOURCE_NOT_QUALIFIED",
            live_dispatch_allowed=True, scope=receipt.get('scope', "SCOPED_SOURCE_ONLY"),
            plan_sha256=public.plan_sha256, original_plan_sha256=original.plan_sha256,
            parent_receipt_sha256=public.parent_receipt_sha256, descriptor_count=len(public.descriptors),
            total_theoretical_max=planned, maximum_attempts=maximum, retries=0,
            full22_native=False, D01_D02=False, model_use=False)
        with _LOCK:
            if parent in _CLAIMED_PARENTS:
                raise ValueError("scoped_parent_dispatch_lifetime_already_claimed")
            _CLAIMED_PARENTS[parent] = True
            self._initialize(root=root, secrets=secrets)

    def _require_parent(self):
        receipt = parent_owner.resolve_parent(self._parent, plan=self._original)
        if digest(receipt) != self.plan.parent_receipt_sha256:
            raise SourceSafetyStop("scoped_live_parent_binding_changed")
        if self.plan.original_plan() != self._original:
            raise SourceSafetyStop("scoped_plan_changed")
        if self.maximum_attempts != receipt["maximum_attempts"]:
            raise SourceSafetyStop("scoped_parent_budget_changed")

    @staticmethod
    def _category(descriptor):
        if descriptor.endpoint_operation == "credential_exchange":
            return "auth"
        for prefix in ("stock", "completed_close", "us_market", "kr_market", "identity"):
            if descriptor.consumer_role.startswith(prefix + ":"):
                return prefix
        raise SourceSafetyStop("scoped_request_category_unclassified")

    def _authorize_physical(self, request):
        if self.halted or self._active is None:
            raise SourceSafetyStop("scoped_physical_call_outside_execution")
        self._require_parent()
        parent_owner.require_worker_dispatch(self._parent)
        descriptor, expected = self._active
        parent_owner.authorize_descriptor(self._parent, descriptor, plan=self._original)
        if len(request.content) > 16384 or wire_identity(request, self.secrets) != expected:
            raise SourceSafetyStop("scoped_physical_wire_not_bound")
        try:
            _readonly_wire(json.loads(expected), descriptor.endpoint_operation)
        except (ValueError, KeyError, TypeError) as exc:
            raise SourceSafetyStop("scoped_physical_route_denied") from exc
        return descriptor

    async def execute(self, logical_id, request, *, transport, normalize):
        with _LOCK:
            if self._busy or self.halted:
                raise SourceSafetyStop("scoped_concurrent_or_stopped_dispatch")
            self._require_parent()
            descriptor = next((d for d in self.plan.descriptors if d.logical_request_id == logical_id), None)
            if descriptor is None:
                raise SourceSafetyStop("scoped_unplanned_descriptor")
            parent_owner.authorize_descriptor(self._parent, descriptor, plan=self._original)
            expected, _, _ = self.resolve(logical_id)
            self._active, self._busy = (descriptor, expected), True
        try:
            result = await super().execute(logical_id, request,
                transport=_PhysicalKiwoomTransport(self, transport), normalize=normalize)
            self._require_parent()
            if self._http_stop is not None:
                raise SourceSafetyStop("scoped_http_authorization_or_quota_stop")
            if result['status'] != 'PASS' and result.get('attempts'):
                last = result['attempts'][-1]
                if last.get('status') == 200 and last.get('artifact'):
                    payload = json.loads((self.root / last['artifact']).read_bytes())
                    if not isinstance(payload, dict):
                        raise SourceSafetyStop('scoped_paced_payload_shape_stop')
                    rejected = (str(payload.get('return_code', '0')) not in {'0', ''}
                                or (descriptor.endpoint_operation == 'credential_exchange'
                                    and payload.get('exchange_succeeded') is not True))
                    if rejected:
                        # Keep the original failure body/receipt, but do not
                        # spend further requests after an explicit provider denial.
                        raise SourceSafetyStop('scoped_provider_rejection_stop')
            if self._account_pacer is not None and result['status'] != 'PASS':
                raise SourceSafetyStop('scoped_paced_normalization_stop')
            if self._account_pacer is not None and descriptor.endpoint_operation == 'usa20590':
                from datetime import date, datetime
                from app.services.source_value_quality import strict_close_quality
                from app.services.market_session import us_market_session
                target = date.fromisoformat(descriptor.target_period)
                when = datetime.fromisoformat(result['attempts'][-1]['started_at'])
                if any(us_market_session(at).latest_completed_regular_session_date != target
                       for at in (self.plan.frozen_at, when)):
                    raise SourceSafetyStop('scoped_paced_completed_session_stop')
                from app.services.sealed_fresh_dispatch import consume_bound_result
                consume_bound_result(root=self.root,plan=self.plan,logical_id=logical_id,
                    receipt_sha256=result['receipt_sha256'])
                denial=strict_close_quality((self.root / descriptor.raw_path).read_bytes(),target=target,
                    logical_request_id=logical_id,observed_at=result['retrieval_time'])
                if denial is not None:
                    public=denial.model_dump(mode='json')
                    self._save('source-quality/'+logical_id+'.json',public)
                    self.role_quality_denials[logical_id]=denial
                    # PASS here is sealed HTTP-fragment custody, not price use.
                    result=dict(result,source_quality=public)
            return result
        except BaseException:
            self.halted = True
            if self._account_pacer is not None:
                try:
                    parent_owner.revoke_parent(self._parent)
                except ValueError:
                    pass  # Already revoked/expired; never recreate authority.
                if self._pacing_context is None:
                    await self._account_pacer.halt()
            raise
        finally:
            if self._pacing_context is not None:
                context, pacing = self._pacing_context
                self._pacing_context = None
                pacing['stopped'] = self.halted
                # Keep the account lock until semantic/source normalization
                # has either passed or globally stopped this scoped route.
                await context.__aexit__(None, None, None)
            self._active, self._busy = None, False

    async def reject_unbound_wire(self):
        """An identity violation before IO is not a benign source-value denial."""
        self._require_parent()
        self.halted=True
        if self._account_pacer is not None and self._pacing_context is None:
            await self._account_pacer.halt()

    def skip_unselected(self, logical_id):
        self._require_parent()
        return super().skip_unselected(logical_id)

    def physical_accounting(self):
        return dict(physical_attempts=self.physical_attempts, maximum_attempts=self.maximum_attempts,
            mutually_exclusive_categories=dict(self._counts), halted=self.halted,
            http_stop=self._http_stop, no_automatic_retries=True)
