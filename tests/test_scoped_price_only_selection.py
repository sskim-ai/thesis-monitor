"""Price-only selection uses original authority, never chart/Native coverage."""
from types import SimpleNamespace

import pytest

from app.services import current_scoped_source_owner as owner
from app.services.current_scoped_source_results import _completed_close_inputs
from app.services.completed_price_state import required_source_slot
from app.services.scoped_source_plan import ScopedConfig
from test_current_scoped_source_owner import setup_parent, wire


def selected(tmp_path, index=0):
    args, _, identities = setup_parent(tmp_path, three_types=True)
    value = args['spec'].config.model_dump(mode='json')
    value['capture_selection'] = dict(contract='scoped-price-capture-selection-v1',
        close_security_ids=[value['subjects'][index]['security_id']])
    spec = args['spec'].model_copy(update={'config': ScopedConfig.model_validate(value)})
    return dict(args, spec=spec, plan=wire(spec, identities)), identities


@pytest.mark.parametrize('index', [0, 1])
def test_registered_ordinary_ads_price_only_original_parent(tmp_path, index):
    args, _ = selected(tmp_path, index)
    subject = args['spec'].config.subjects[index]
    parent = owner.issue_parent(**args)
    receipt = owner.resolve_parent(parent, plan=args['plan'])
    assert receipt['current_source_evidence'] == 'NOT_ISSUED'
    assert not receipt['full22_native'] and not receipt['financial_use']
    assert [(d.endpoint_operation, d.subject) for d in args['plan'].descriptors] == [
        ('credential_exchange', 'run'), ('usa20590', subject.ticker)]
    stock = SimpleNamespace(run_id=args['spec'].generation_id, frozen_at=args['spec'].cutoff)
    price_plan, reads = _completed_close_inputs(args['spec'], stock)
    assert len(reads) == 1 and reads[0].canonical_security_id == subject.security_id
    assert not price_plan.model_dump()['chart_coverage_granted']
    assert required_source_slot(args['plan'], reads[0]).subject == subject.ticker
    assert owner.resolve_parent(parent, plan=args['plan']) == receipt
    owner.revoke_parent(parent)
    with pytest.raises(ValueError): owner.resolve_parent(parent)


@pytest.mark.parametrize('mutation', ['unknown', 'kr', 'empty', 'duplicate', 'space',
    'chart', 'market', 'disable_close', 'v1', 'v2', 'shrunk_registration'])
def test_wrong_scope_never_issues_parent(tmp_path, mutation):
    args, identities = selected(tmp_path)
    config = args['spec'].config.model_dump(mode='json')
    selection = config['capture_selection']
    if mutation == 'unknown': selection['close_security_ids'] = ['not-registered']
    elif mutation == 'kr': selection['close_security_ids'] = [config['subjects'][2]['security_id']]
    elif mutation == 'empty': selection['close_security_ids'] = []
    elif mutation == 'duplicate': selection['close_security_ids'] *= 2
    elif mutation == 'space': selection['close_security_ids'][0] += ' '
    elif mutation == 'chart': selection['stock_roles'] = ['adjusted_daily']
    elif mutation == 'market': selection['market_contexts'] = ['us']
    elif mutation == 'disable_close': selection['us_completed_closes'] = False
    elif mutation in ('v1', 'v2'): selection['contract'] = 'scoped-capture-selection-' + mutation
    else:
        config['subjects'] = config['subjects'][:1]
        spec = args['spec'].model_copy(update={'config': ScopedConfig.model_validate(config)})
        plan = wire(spec, {config['subjects'][0]['ticker']: identities[config['subjects'][0]['ticker']]})
        with pytest.raises(ValueError): owner.issue_parent(**dict(args, spec=spec, plan=plan))
        return
    with pytest.raises(ValueError): ScopedConfig.model_validate(config)


@pytest.mark.parametrize('field,value', [('exchange', 'WRONG'), ('subject', 'OTHER'),
    ('latest_completed_session', '1999-01-01')])
def test_original_price_slot_rejects_identity_or_session_mutation(tmp_path, field, value):
    args, _ = selected(tmp_path)
    stock = SimpleNamespace(run_id=args['spec'].generation_id, frozen_at=args['spec'].cutoff)
    _, reads = _completed_close_inputs(args['spec'], stock)
    changed = reads[0].model_copy(update={field: value})
    if field == 'subject':
        assert required_source_slot(args['plan'], changed) is None
    else:
        with pytest.raises(ValueError): required_source_slot(args['plan'], changed)


@pytest.mark.parametrize('index', [0, 1])
def test_price_only_original_dispatch_and_consumer_without_chart(tmp_path, index):
    import httpx
    import json
    from app.services import current_scoped_source_results as replay
    from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
    from app.services.scoped_source_plan import compile_scoped_wire_contract
    from app.services.kiwoom_completed_close_owner import OFFICIAL_SPEC_SHA256
    from tests.completed_price_fixtures import official_spec
    from test_current_scoped_source_dispatch import execute
    args, identities = selected(tmp_path, index)
    parent = owner.issue_parent(**args)
    spec = args['spec']
    dispatcher = CurrentScopedDispatcher(parent=parent,plan=args['plan'],root=tmp_path/'dispatch',
        owners={d.normalizer:d.owner_sha256 for d in args['plan'].descriptors},
        config_identities={'kiwoom':spec.provider_config_sha256},credential_presence={'kiwoom':True},secrets=())
    wire_value = compile_scoped_wire_contract(config=spec.config,identities=identities,generation_id=spec.generation_id,
        at=spec.cutoff,code_sha=spec.code_sha,provider_config_sha256=spec.provider_config_sha256,retries=0)
    assert not wire_value['stock_reads']
    stock=dict(contract='current-scoped-stock-capture-v1',run_id=spec.generation_id,
        acquisition_id=spec.generation_id+'-stock',frozen_at=spec.cutoff.isoformat(),reads=[],
        owner_files=json.loads(wire_value['owner_files_json']))
    worker=tmp_path/'worker';worker.mkdir()
    descriptor=next(d for d in dispatcher.plan.descriptors if d.endpoint_operation=='usa20590')
    row=dict(dt=descriptor.target_period.replace('-',''),cur_prc='105',open_pric='104',high_pric='106',low_pric='103')
    execute(dispatcher,descriptor,httpx.MockTransport(lambda request:httpx.Response(200,json=dict(return_code=0,result_list=[row]))))
    document=dispatcher.root/'official-spec.json';document.write_bytes(official_spec())
    inputs=dict(parent=parent,wire=wire_value,stock_plan=stock,dispatcher=dispatcher,
        capture_root=dispatcher.root,worker_root=worker,
        market_results={'completed_close_documentation':dict(path=document.name,sha256=OFFICIAL_SPEC_SHA256)})
    result=replay.examine(**inputs)
    price=result['completed_closes'][descriptor.subject]
    assert price['state']['state']=='AVAILABLE',price
    assert price['state']['numeric_owner']['contract']=='kiwoom-us-completed-session-price-v2'
    assert not result['stock_roles'] and not result['source_only_roles_issued']
    assert not price['technical_injection'] and not price['economic_use'] and not result['full22_native']
    assert replay.examine(**inputs)==result
    with pytest.raises(ValueError): replay.examine(**dict(inputs,parent=owner.CurrentScopedSourceParent()))
    owner.revoke_parent(parent)
    with pytest.raises(ValueError): replay.examine(**inputs)


@pytest.mark.parametrize('index', [0, 1, 2])
@pytest.mark.parametrize('role,count,api_us,api_kr,adjusted', [
    ('adjusted_daily',1000,'usa06012','ka10081',True),
    ('adjusted_weekly',700,'usa06013','ka10082',True),
    ('adjusted_monthly',300,'usa06014','ka10083',True),
    ('unadjusted_weekly_valuation',300,'usa06013','ka10082',False)])
def test_four_original_roles_use_role_specific_producer(tmp_path,index,role,count,api_us,api_kr,adjusted):
    from app.services.scoped_source_plan import compile_scoped_wire_contract
    args,_,identities=setup_parent(tmp_path,three_types=True)
    spec=args['spec'];subject=spec.config.subjects[index]
    value=spec.config.model_dump(mode='json')
    value['capture_selection']=dict(contract='scoped-capture-selection-v2',stock_security_ids=[subject.security_id],
        stock_markets=[subject.market],stock_roles=[role],market_contexts=[],us_completed_closes=False)
    config=ScopedConfig.model_validate(value)
    result=compile_scoped_wire_contract(config=config,identities=identities,generation_id=spec.generation_id,
        at=spec.cutoff,code_sha=spec.code_sha,provider_config_sha256=spec.provider_config_sha256,retries=0)
    read,=result['stock_reads']
    assert (read.count,read.adjusted,read.api_id)==(count,adjusted,api_us if subject.market=='us' else api_kr)
    assert len(result['request_plan'].descriptors)==1+read.max_pages
    assert all(d.transient_retry_max==0 for d in result['request_plan'].descriptors)
