"""Original KR client HTTP -> exact approved private Worker -> original lane."""
import base64,json
import httpx
from app.services.sealed_fresh_dispatch import wire_identity
from app.services.sealed_response_binding import SlotNotSelected
from app.services.unified_live_source_transport import SourceSafetyStop

class MarketWorkerRPC(httpx.AsyncBaseTransport):
    def __init__(self,bridge):self.bridge=bridge

    async def handle_async_request(self,request):
        run=self.bridge.transport.dispatcher;public=wire_identity(request,run.secrets)
        matches=[]
        for descriptor in run.plan.descriptors:
            if descriptor.logical_request_id in run.used:continue
            if descriptor.response_binding and any(p not in run.results for p in descriptor.response_binding.parents):continue
            try:resolved,_,_=run.resolve(descriptor.logical_request_id)
            except SlotNotSelected:continue
            if resolved==public:matches.append(descriptor)
        if len(matches)!=1:
            await run.reject_unbound_wire()
            raise SourceSafetyStop('market_worker_rpc_exact_slot_required')
        result=await self.bridge.command({'market_wire':dict(logical_id=matches[0].logical_request_id,request_json=public)})
        if not isinstance(result.get('status'),int):raise SourceSafetyStop('market_worker_rpc_original_response_required')
        return httpx.Response(result['status'],headers=result['headers'],
            content=base64.b64decode(result['body_b64'],validate=True),request=request)

    async def aclose(self):pass
