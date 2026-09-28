from copy import deepcopy
from datetime import timedelta
import hashlib
import json

import pytest

from app.services.bounded_financial_acquisition import make_plan
from app.services.fresh_source_run_contract import (
    acquisition_plan, reject_current_carryin, validate_fresh_receipt, validate_local_seed,
)
from app.services.unified_stock_acquisition import UNIVERSE
from test_unified_stock_acquisition import plan as stock_fixture


@pytest.fixture(name='stock_plan')
def fresh_stock_plan():
    return stock_fixture.__wrapped__()


def identities():
    return {ticker: dict(ticker=ticker, canonical_company_id='issuer-'+ticker,
        canonical_security_id='security-'+ticker, identity_provider='fixture',
        cik=str(1000+i), corp_code=f'{1000+i:08d}', issuer_type='domestic_us')
        for i, ticker in enumerate(t for ts in UNIVERSE.values() for t in ts)}


def test_exact_all22_budgets_have_no_retained_exemption(stock_plan):
    result = acquisition_plan(stock_plan, identities(), kr_max_pages=4)
    assert len(result['financial_plans']) == 22 and result['retained_subjects'] == []
    assert len(result['stock_plan']['reads']) == 88
    assert result['night_scope']['products'] == ['KOSPI200']
    assert result['dispatch_allowed'] is False
    assert result['plan_stage'] == 'OFFLINE_CANDIDATE_NOT_QUALIFIED'
    for ticker in ('SNDK', '005930', '047810'):
        assert result['financial_plans'][ticker]['ticker'] == ticker
    for budget in result['budgets'].values():
        assert budget['maximum_HTTP_attempts'] == budget['maximum_logical'] * 3
        assert budget['maximum_logical'] > 0 and budget['semantic_retries'] == 0
    assert result == acquisition_plan(stock_plan, identities(), kr_max_pages=4)


@pytest.mark.parametrize('cap', [None, 0, -1, 21, True, 2.5])
def test_undefined_or_unbounded_pages_fail_before_network(stock_plan, cap):
    with pytest.raises(ValueError, match='page_cap'):
        acquisition_plan(stock_plan, identities(), kr_max_pages=cap)


def test_all22_identity_coverage_fail_closed(stock_plan):
    rows = identities()
    del rows['SNDK']
    with pytest.raises(ValueError, match='exact_22'):
        acquisition_plan(stock_plan, rows, kr_max_pages=2)


def test_historical_retained_default_is_not_silently_changed(stock_plan):
    with pytest.raises(ValueError):
        make_plan(identities()['SNDK'], market='us', cutoff=stock_plan.frozen_at, run_id='test')


@pytest.mark.parametrize('key', ['parent_zip_sha256', 'old_quality_bundle', 'prior_model_output',
    'versioned_binding', 'persisted_binding', 'old_macro_observation', 'accepted_stock_packet'])
@pytest.mark.parametrize('encoded', [False, True])
def test_prior_mutable_carryin_rejected_even_in_json_string(key, encoded):
    value = {key: 'old'}
    with pytest.raises(ValueError):
        reject_current_carryin({'nested': json.dumps(value) if encoded else [value]})


def test_static_seed_only():
    seed = dict(contract='unified-local-seed-projection-v1', denials=[], roles={
        'thesis': {'records': [{'table': 'investmentthesis', 'record': {'logic': 'business'}}]}})
    validate_local_seed(seed)
    seed['roles']['thesis']['records'][0]['table'] = 'financialsnapshot'
    with pytest.raises(ValueError, match='mutable_table'):
        validate_local_seed(seed)


def test_current_receipt_identity_time_bytes_and_path(stock_plan, tmp_path):
    at = stock_plan.frozen_at
    (tmp_path/'source.json').write_bytes(b'{"fixture":true}')
    receipt = dict(run_id=stock_plan.run_id, acquisition_class='FRESH_CURRENT_RUN',
        requested_at=at.isoformat(), received_at=(at+timedelta(seconds=1)).isoformat(),
        artifact='source.json', source_sha256=hashlib.sha256(b'{"fixture":true}').hexdigest())
    def check(row):
        return validate_fresh_receipt(row, root=tmp_path, run_id=stock_plan.run_id,
            started_at=at, cutoff=at+timedelta(seconds=2))
    assert check(receipt)['status'] == 'PASS'
    for key, value in [('run_id', 'old'), ('requested_at', (at-timedelta(seconds=1)).isoformat()),
            ('artifact', '../source.json'), ('source_sha256', '0'*64),
            ('acquisition_class', 'VERSIONED_PERSISTED_ALLOWED')]:
        changed = deepcopy(receipt)
        changed[key] = value
        with pytest.raises(ValueError):
            check(changed)
    (tmp_path/'link').symlink_to(tmp_path/'source.json')
    with pytest.raises(ValueError):
        check({**receipt, 'artifact': 'link'})
