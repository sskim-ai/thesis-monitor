"""HTTP adapter used only by the opted-in, whole-plan-admitted collector."""
import json

import httpx

from app.services.sealed_fresh_dispatch import consume_bound_result, wire_identity
from app.services.sealed_response_binding import SlotNotSelected
from app.services.unified_live_source_transport import SourceSafetyStop


class CapturedFragment:
    def __init__(self, descriptor):
        self.identity = (descriptor.normalizer, descriptor.owner_sha256)
        self.descriptor = descriptor

    def __call__(self, raw):
        if not raw:
            raise ValueError('empty_source_fragment')
        if self.descriptor.provider == 'kiwoom':
            payload = json.loads(raw)
            if not isinstance(payload, dict) or str(payload.get('return_code', '0')) not in {'0', ''}:
                raise ValueError('kiwoom_source_status_denied')
        return dict(value={'bytes': len(raw), 'source_fact_qualified': False},
            source_period='SOURCE_FRAGMENT_PENDING_NATIVE_OWNER', consumer_complete=True)


class SealedSourceTransport(httpx.AsyncBaseTransport):
    """No client retry or implicit provider routing; native owners parse results."""
    def __init__(self, dispatcher, inner, *, providers):
        self.dispatcher, self.inner, self.providers = dispatcher, inner, frozenset(providers)
        self.auth_request_hash = None
        self.auth_reuses = 0

    async def handle_async_request(self, request):
        run = self.dispatcher
        if run.halted:
            raise SourceSafetyStop('systemic_stop_latched')
        public = wire_identity(request, run.secrets)
        auth = str(request.url) == 'https://api.kiwoom.com/oauth2/token'
        if auth and run.credential_response is not None:
            if public != self.auth_request_hash:
                raise SourceSafetyStop('credential_reuse_identity_mismatch')
            self.auth_reuses += 1
            return httpx.Response(200, content=run.credential_response.content, request=request)
        matches = []
        for d in run.plan.descriptors:
            if d.provider not in self.providers or d.logical_request_id in run.used:
                continue
            template = json.loads(d.request_json)
            route = httpx.URL(template['url'])
            if (template['method'], route.host, route.path) != (request.method, request.url.host, request.url.path):
                continue
            if request.method == 'POST':
                body, planned = json.loads(request.content), json.loads(template['body'])
                if (dict(template['headers']).get('api-id') != request.headers.get('api-id')
                        or planned.get('stk_cd') != body.get('stk_cd')):
                    continue
            if d.response_binding and any(k not in run.results for k in d.response_binding.parents):
                continue
            try:
                resolved, _, _ = run.resolve(d.logical_request_id)
            except SlotNotSelected:
                continue
            if resolved == public:
                matches.append(d)
        if len(matches) != 1:
            raise SourceSafetyStop('native_request_not_unique_sealed_slot')
        d = matches[0]
        final = await run.execute(d.logical_request_id, request, transport=self.inner, normalize=CapturedFragment(d))
        if final['status'] != 'PASS':
            last = final['attempts'][-1]
            # Returning an invented 502 would erase an owner's original failure.
            if last['status'] is None:
                raise httpx.TransportError('sealed_transport_failed', request=request)
            raw = (run.root / last['artifact']).read_bytes() if last.get('artifact') else b''
            return httpx.Response(last['status'], content=raw, request=request)
        consume_bound_result(root=run.root, plan=run.plan, logical_id=d.logical_request_id,
                             receipt_sha256=final['receipt_sha256'])
        if auth:
            self.auth_request_hash = public
            raw = run.credential_response.content
        else:
            raw = (run.root / d.raw_path).read_bytes()
        return httpx.Response(200, content=raw, headers=final['response_headers'], request=request)

    async def aclose(self):
        # Native providers own short-lived clients; the run owns the one transport.
        pass

    async def shutdown(self):
        await self.inner.aclose()
