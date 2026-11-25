"""Date-only unavailable notices through the actual US market renderer."""
from copy import deepcopy
from datetime import datetime, timedelta
import socket
from types import SimpleNamespace

import pytest

from app.services import production_message_renderer as renderer
from app.services.canonical_market_projection import project_optional_night
from app.services.unified_snapshot_contract import digest
from scripts import m12ds_r4_r4_market as consumer
from tests.night_owner_fixtures import night_fixture
from tests.test_c47_optional_night_market import parts, project, reseal, decision


@pytest.fixture(autouse=True)
def no_live_io(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('C53_AVAILABILITY_NO_REAL_NETWORK')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)


def evaluate(night):
    night['value_sha256'] = digest(night['value'])
    seed = dict(parent_run_id=night['original_run_id'], started_at=night['observed_at'],
        run_acquisitions={'night': night['value_sha256']})
    return project_optional_night(night, seed=seed,
        cutoff=datetime.fromisoformat(night['observed_at']) + timedelta(minutes=2))


def actual_message(data):
    projected = project(data)
    output = decision(projected['context'])
    assert consumer.validate_market(output, projected['context'])['status'] == 'PASS'
    message = renderer.market_message(SimpleNamespace(market='us', gen='C53-synthetic',
        projected={'us': projected}, markets={'us': output}, fresh_stocks={}))
    return projected, message['text']


def test_stale_pair_reaches_real_renderer_as_dates_without_old_prices_or_direction():
    data = parts(night_case='stale')
    before = deepcopy(data)
    night = data[2]['night']
    expected = night['value']['telemetry']['expected_reference_date']
    returned = night['value']['observations'][0]['raw_payload']['session_date']
    projected, text = actual_message(data)
    source = projected['packet']['market_context']
    assert source['night_futures'] == []
    assert not any(f['fact_type'].startswith('night_futures') for f in source['fact_catalog'])
    notice = text.split('한국 야간선물 · KOSPI200', 1)[1]
    assert '최신 세션 미확보' in notice
    assert '필요 KRX 기준일: ' + expected in notice
    assert '이번 수집에서 확인한 야간 기준일: ' + returned in notice
    assert '이번 야간 방향 판단에서 제외' in notice
    assert '110' not in notice and '%' not in notice
    assert 'SPY' in text and '시장 판단:' in text
    output = decision(projected['context'])
    output['rates_or_macro_context'] = '한국 야간선물 상승은 위험 선호를 뒷받침합니다.'
    assert consumer.validate_market(output, projected['context'])['status'] == 'FAIL'
    assert data == before


def test_returned_current_raw_date_is_not_misreported_as_only_an_old_pair():
    packet, seed, graph = parts(night_case='stale')
    night = graph['night']
    expected = night['value']['telemetry']['expected_reference_date']
    night['value']['telemetry']['returned_night_session_dates'] = [expected]
    night['value_sha256'] = digest(night['value'])
    seed['run_acquisitions']['night'] = night['value_sha256']
    reseal(packet, seed, graph)
    projected, text = actual_message((packet, seed, graph))
    detail = projected['packet']['market_context']['night_futures_ownership']['date_only_detail']
    assert detail['latest_returned_krx_reference_date'] == expected
    assert detail['latest_date_source'] == 'parsed_night_rows'
    assert '기준일에 맞는 확정 수치 미확보' in text
    assert '이번 수집에서 확인한 야간 기준일: ' + expected in text
    assert not projected['packet']['market_context']['night_futures']


def test_empty_response_does_not_invent_a_returned_night_date():
    projected, text = actual_message(parts())
    detail = projected['packet']['market_context']['night_futures_ownership']['date_only_detail']
    assert detail['latest_returned_krx_reference_date'] is None
    assert detail['latest_date_source'] is None
    assert '이번 수집에서 확인한 야간 기준일: 미확보' in text


@pytest.mark.parametrize('invalid', ['2099-01-01', '2026-99-99', '2026-01-01'])
def test_future_malformed_and_unqueried_dates_are_not_displayed_as_confirmed(invalid):
    night = night_fixture('2026-11-25T08:10:00+09:00')
    night['value']['telemetry']['returned_night_session_dates'] = [invalid]
    rows, receipt = evaluate(night)
    assert not rows
    assert receipt['date_only_detail']['required_krx_reference_date'] == '2026-11-25'
    assert receipt['date_only_detail']['latest_returned_krx_reference_date'] is None


@pytest.mark.parametrize('at,case,state', [
    ('2026-11-25T08:10:00+09:00', 'available', 'AVAILABLE_FINAL'),
    ('2026-11-25T05:59:59+09:00', 'empty', 'UNAVAILABLE_BEFORE_FINALITY'),
])
def test_available_and_before_finality_receipts_keep_their_existing_shape(at, case, state):
    rows, receipt = evaluate(night_fixture(at, case=case))
    assert receipt['state'] == state
    assert bool(rows) == (case == 'available')
    assert 'date_only_detail' not in receipt
