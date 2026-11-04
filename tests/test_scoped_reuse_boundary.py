"""Historical bytes are not current capabilities; original boundaries stay shut."""
import json

import httpx
import pytest

from app.services import current_scoped_source_results as replay
from app.services import current_scoped_source_owner as owner
from app.services.unified_live_source_transport import SourceSafetyStop
from test_current_scoped_source_results import capture, setup_parent
from test_current_scoped_source_dispatch import execute


def test_rehashed_historical_input_cannot_bind_current_capture(capture):
    args,bridge,_=capture
    data=json.loads(bridge.frozen.read_bytes())
    data['historical_source_root']=str(args['worker_root']/'stocks')
    bridge.frozen.write_text(json.dumps(data))
    bridge.sha=replay._sha(bridge.frozen.read_bytes())
    with pytest.raises(ValueError,match='scoped_current_original_worker_config_required'):
        replay.bind_capture(**args,worker_bridge=bridge)
    assert args['dispatcher'].physical_attempts==0
    assert args['dispatcher'] not in replay._CAPTURES


@pytest.mark.parametrize('successful_before',[0,1])
def test_systemic_429_first_or_middle_halts_all_later_descriptors(capture,successful_before):
    args,_,_=capture;run=args['dispatcher']
    descriptors=[d for d in run.plan.descriptors if d.page_ordinal==1 and d.response_binding is None
        and d.endpoint_operation!='credential_exchange']
    calls=[]
    def handle(request):
        calls.append(request)
        return httpx.Response(200 if len(calls)<=successful_before else 429,json={'return_code':0})
    transport=httpx.MockTransport(handle)
    for d in descriptors[:successful_before]:execute(run,d,transport)
    denied=descriptors[successful_before]
    with pytest.raises(SourceSafetyStop):execute(run,denied,transport)
    later=descriptors[successful_before+1]
    with pytest.raises(SourceSafetyStop):execute(run,later,transport)
    assert len(calls)==run.physical_attempts==successful_before+1
    assert later.logical_request_id not in run.results
    assert len(run.results[denied.logical_request_id]['attempts'])==1 and run.halted
    owner.revoke_parent(args['parent'])
