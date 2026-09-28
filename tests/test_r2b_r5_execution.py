from copy import deepcopy
from types import SimpleNamespace

import pytest

from scripts import r2b_r2_contract as c
from scripts.r2b_r5_execution import Execution, add_limits, MAX_CALLS


def test_existing_rows_unchanged_when_limit_schema_composed():
    schema=c.schemas.obj({'cores':c.schemas.obj({'X':c.schemas.obj({'value':{'type':'string'}})})})
    before=deepcopy(schema)
    inputs={'X':dict(mode='EVIDENCE_BASED'), 'Y':dict(mode='UNKNOWN_LIMIT',recovery={'ref':{}})}
    result=add_limits(schema,inputs,['X','Y'])
    assert schema==before and result['properties']['cores']==before['properties']['cores']
    assert result['properties']['limits']['properties']['Y']==c.unknown_schema({'ref':{}})
    assert add_limits(schema,inputs,['X'])==before


def test_first_failure_stops_without_retry():
    calls=[]
    def fail(*args):
        calls.append(1)
        raise ValueError('fixture-failure')
    fake=SimpleNamespace(ledger=[],core=fail,publish=lambda:None)
    with pytest.raises(ValueError,match='fixture-failure'):
        Execution.bounded(fake,'core',dict(market='us',batch=1,subjects=['X']),{})
    assert calls==[1] and fake.ledger[0]['status']=='FAIL'


def test_call_budget_blocks_before_dispatch():
    fake=SimpleNamespace(ledger=[dict(stage='market',attempts=1)]*2)
    with pytest.raises(Exception,match='stage_call_budget'):
        Execution.bounded(fake,'market',dict(market='kr',batch=1,subjects=[]),{})
    assert sum(MAX_CALLS.values())==26
