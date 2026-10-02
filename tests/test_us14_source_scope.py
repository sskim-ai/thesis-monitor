from copy import deepcopy

import pytest

from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import StockPlan, UNIVERSE, coverage
from scripts.r9_rev11_sealed_plan import compile_plan
from scripts.us14_source_scope import require_us14_plan
from tests.test_r9_rev11_full_plan import compiled


def us_plan():
    stock, args, _ = compiled()
    raw = stock.model_dump(mode='json')
    raw['contract'] = 'one-shot-us14-source-acquisition-v1'
    raw['reads'] = [r for r in raw['reads'] if r['market'] == 'us']
    stock = StockPlan.model_validate(raw)
    auxiliary = args['identities']['000660']
    args.update(stock=stock, identities={t: s for t, s in args['identities'].items() if t in UNIVERSE['us']},
        news_reads=[r for r in args['news_reads'] if r.market == 'us'],
        auxiliary_security=auxiliary, auxiliary_identity_sha256='f'*64)
    out = compile_plan(**args)
    frozen = dict(out, plan=out['plan'].model_dump(mode='json'),
        stock_plan=stock.model_dump(mode='json'), scope='US14_ONLY', sessions={'us': '2026-09-22'},
        security_records=list(args['identities'].values()))
    return args, out, frozen


def test_exact_us14_plan_and_declared_financial_only_auxiliary():
    args, out, frozen = us_plan()
    dep = require_us14_plan(frozen)
    assert dep.role == 'AUXILIARY_ISSUER_ONLY'
    assert not any((dep.user_message_eligible, dep.model_subject_eligible, dep.valuation_eligible, dep.technical_eligible))
    assert len(args['stock'].reads) == 56
    assert len(out['candidate']['current_subjects']) == 14
    assert set(out['candidate']['financial_plans']) == set(UNIVERSE['us']) | {'000660'}
    assert all(d.consumer_role == 'financial:000660' for d in out['plan'].descriptors if d.subject == '000660')
    assert not out['candidate']['kr_market_reads']
    assert 'kr_market_wire' not in out['candidate']['budgets']
    assert out['plan'].admission(rev10_receipt=args['rev10_receipt'], owners=out['owners'],
        config_identities=args['config_identities'], credential_presence={k: True for k in args['config_identities']})['live_dispatch_allowed']
    rows = [dict(entry_id=r.entry_id, status='PASS') for r in args['stock'].reads]
    assert coverage(args['stock'], rows)['complete']
    with pytest.raises(ValueError, match='us14_result'):
        coverage(args['stock'], rows[:-1])


@pytest.mark.parametrize('kind', ['missing', 'duplicate', 'kr-role'])
def test_us14_cannot_relax_exact_primary_read_set(kind):
    args, _, _ = us_plan()
    raw = args['stock'].model_dump(mode='json')
    if kind == 'missing':
        raw['reads'].pop()
    elif kind == 'duplicate':
        raw['reads'].append(raw['reads'][0])
    else:
        all_plan, _, _ = compiled()
        raw['reads'].append(next(r.model_dump(mode='json') for r in all_plan.reads if r.market == 'kr'))
    with pytest.raises(ValueError, match='exact_us14'):
        StockPlan.model_validate(raw)


@pytest.mark.parametrize('mutation', ['scope', 'session', 'primary', 'aux-model', 'aux-price',
    'aux-generation', 'aux-hash', 'missing-aux', 'kr-market', 'news', 'security'])
def test_us14_scope_fails_closed(mutation):
    _, _, f = us_plan()
    c = f['candidate']
    if mutation == 'scope':
        f['scope'] = 'ALL22'
    elif mutation == 'session':
        f['sessions']['kr'] = '2026-09-23'
    elif mutation == 'primary':
        c['current_subjects'].append('000660')
    elif mutation == 'aux-model':
        c['auxiliary_issuer_dependencies']['000660']['model_subject_eligible'] = True
    elif mutation == 'aux-price':
        c['auxiliary_issuer_dependencies']['000660']['technical_eligible'] = True
    elif mutation == 'aux-generation':
        c['auxiliary_issuer_dependencies']['000660']['run_id'] = 'old'
    elif mutation == 'aux-hash':
        c['auxiliary_issuer_dependencies']['000660']['source_plan_sha256'] = '0'*64
    elif mutation == 'missing-aux':
        c['auxiliary_issuer_dependencies'] = {}
    elif mutation == 'kr-market':
        c['kr_market_reads'] = [{}]
    elif mutation == 'news':
        f['news_reads'][0]['subject'] = '000660'
    else:
        f['security_records'].append(deepcopy(f['security_records'][0]))
    c['plan_sha256'] = digest({k: v for k, v in c.items() if k != 'plan_sha256'})
    with pytest.raises(ValueError):
        require_us14_plan(f)


def test_missing_auxiliary_cannot_be_implicitly_loaded():
    args, _, _ = us_plan()
    args.pop('auxiliary_security')
    with pytest.raises(ValueError, match='auxiliary'):
        compile_plan(**args)
