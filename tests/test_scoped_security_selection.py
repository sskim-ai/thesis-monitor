"""Subset capture never substitutes for full registration or source authority."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from app.services import current_scoped_source_owner as owner
from app.services.scoped_source_plan import ScopedCaptureSelection, ScopedConfig
from test_current_scoped_source_owner import setup_parent, wire


def selected(args, identities, ids):
    spec = args['spec']
    value = spec.config.model_dump(mode='json')
    value['capture_selection'] = dict(contract='scoped-capture-selection-v2',
        stock_security_ids=ids, stock_markets=['kr', 'us'],
        stock_roles=['adjusted_daily'], market_contexts=[], us_completed_closes=True)
    spec = spec.model_copy(update={'config': ScopedConfig.model_validate(value)})
    return dict(args, spec=spec, plan=wire(spec, identities))


@pytest.mark.parametrize('index', [0, 1, 2])
def test_unseen_ordinary_ads_kr_same_qualification(tmp_path, index):
    args, _, ids = setup_parent(tmp_path, three_types=True)
    subject = args['spec'].config.subjects[index]
    args = selected(args, ids, [subject.security_id])
    parent = owner.issue_parent(**args)
    receipt = owner.resolve_parent(parent, plan=args['plan'])
    assert receipt['current_source_evidence'] == 'NOT_ISSUED'
    assert not receipt['full22_native'] and not receipt['financial_use']
    chart = [d for d in args['plan'].descriptors if d.endpoint_operation in ('usa06012', 'ka10081')]
    assert chart and {d.subject for d in chart} == {subject.ticker}
    closes = [d for d in args['plan'].descriptors if d.endpoint_operation == 'usa20590']
    assert {d.subject for d in closes} == {'NEWUS', 'NEWADS'}
    assert owner.resolve_parent(parent, plan=args['plan']) == receipt
    owner.revoke_parent(parent)
    with pytest.raises(ValueError): owner.resolve_parent(parent)


@pytest.mark.parametrize('mutation', ['unknown', 'duplicate', 'empty', 'wrong_market', 'v1_label', 'forged_plan', 'shrink_registration'])
def test_untrusted_subset_cannot_expand_or_impersonate_parent(tmp_path, mutation):
    args, _, ids = setup_parent(tmp_path, three_types=True)
    selected_id = args['spec'].config.subjects[0].security_id
    args = selected(args, ids, [selected_id])
    if mutation == 'forged_plan':
        (tmp_path / 'other').mkdir()
        original, _, _ = setup_parent(tmp_path / 'other', three_types=True)
        with pytest.raises(ValueError): owner.issue_parent(**dict(args, plan=original['plan']))
        return
    config = args['spec'].config.model_dump(mode='json')
    sel = config['capture_selection']
    if mutation == 'unknown': sel['stock_security_ids'] = ['UNREGISTERED']
    if mutation == 'duplicate': sel['stock_security_ids'] *= 2
    if mutation == 'empty': sel['stock_security_ids'] = []
    if mutation == 'wrong_market': sel['stock_markets'] = ['kr']
    if mutation == 'v1_label': sel['contract'] = 'scoped-capture-selection-v1'
    if mutation == 'shrink_registration':
        config['subjects'] = config['subjects'][:1]
        spec = args['spec'].model_copy(update={'config': ScopedConfig.model_validate(config)})
        plan = wire(spec, {config['subjects'][0]['ticker']: ids[config['subjects'][0]['ticker']]})
        with pytest.raises(ValueError): owner.issue_parent(**dict(args, spec=spec, plan=plan))
    else:
        with pytest.raises(ValueError): ScopedConfig.model_validate(config)


def test_v1_default_serialization_unchanged():
    value = ScopedCaptureSelection().model_dump(mode='json')
    assert value['contract'] == 'scoped-capture-selection-v1'
    assert 'stock_security_ids' not in value


def test_selected_identity_and_scope_pinned_not_mutable(tmp_path):
    args, _, ids = setup_parent(tmp_path, three_types=True)
    args = selected(args, ids, [args['spec'].config.subjects[0].security_id])
    parent = owner.issue_parent(**args)
    changed = deepcopy(args['spec'].model_dump(mode='json'))
    changed['config']['capture_selection']['stock_security_ids'].append(args['spec'].config.subjects[1].security_id)
    with pytest.raises(ValueError):
        owner.issue_parent(**dict(args, spec=changed))
    assert owner.resolve_parent(parent)['current_source_evidence'] == 'NOT_ISSUED'
    owner.revoke_parent(parent)


def test_close_only_adapter_declares_no_chart_coverage_and_exact_membership(tmp_path):
    from app.services.current_scoped_source_results import _completed_close_inputs
    from app.services.completed_price_state import required_source_slot
    args, _, ids = setup_parent(tmp_path, three_types=True)
    args = selected(args, ids, [args['spec'].config.subjects[2].security_id])
    spec = args['spec']
    stock = SimpleNamespace(run_id=spec.generation_id, frozen_at=spec.cutoff)
    plan, reads = _completed_close_inputs(spec, stock)
    assert {r.subject for r in reads} == {'NEWUS', 'NEWADS'}
    assert not plan.model_dump()['chart_coverage_granted']
    assert plan.model_dump()['contract'] == 'current-scoped-completed-price-plan-v1'
    for read in reads:
        assert read in plan.reads
        assert required_source_slot(args['plan'], read).subject == read.subject
        with pytest.raises(ValueError):
            required_source_slot(args['plan'], read.model_copy(update={'exchange': 'WRONG'}))
