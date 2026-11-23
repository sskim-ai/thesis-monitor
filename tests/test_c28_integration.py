"""New C28 integration boundaries only; no real Owner, DB, network, or model."""
import asyncio
from copy import deepcopy
from dataclasses import replace
from datetime import datetime as DateTime, timedelta
import fcntl
import json
import socket

import pytest

from app.jobs import unified_market_snapshot as job
from app.macro.providers.krx import sealed_night_end_date_history
from app.services.model_execution_plan import compile_model_plan
from app.services.unified_market_run import target_session
from app.services.unified_snapshot_contract import digest
from tests.test_c22z_dynamic_model_plan import cohort
from tests.test_local_launchd_entry import configuration, code_pin
from tests.test_r2b_r5_market_adapter import fixture, project
from tests.night_owner_fixtures import night_fixture

TAG = 'us-20261121-c28d7e1f'
START = DateTime.fromisoformat('2026-11-21T11:00:00+09:00')


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('C28_TEST_EXTERNAL_IO_DENIED')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)


def clock(monkeypatch, at):
    class FixedDateTime(DateTime):
        @classmethod
        def now(cls, tz=None):
            return at.astimezone(tz) if tz else at.replace(tzinfo=None)
    monkeypatch.setattr(job, 'datetime', FixedDateTime)


def test_c25_0810_cohort_compiles_with_preserved_utc_instant():
    value = cohort(us=1, kr=0)
    cutoff = '2026-11-20T23:10:05+00:00'
    value = replace(value, assessment_date='2026-11-21', effective_at=cutoff, cutoff=cutoff,
        subjects=tuple(replace(row, available_at=cutoff) for row in value.subjects))
    plan = compile_model_plan(value, topology='CANONICAL_PRODUCTION')
    assert value.cutoff == cutoff and plan.cohort.sha256 == value.sha256
    with pytest.raises(ValueError, match='SOURCE_OWNER_REQUIRED'):
        value.verify_source_owner(None)
    for change, error in ((dict(assessment_date='2026-11-22'), 'future_assessment'),
            (dict(cutoff='2026-11-20T23:10:05'), 'aware_time_required'),
            (dict(subjects=tuple(replace(row, available_at='2026-11-20T23:10:06Z') for row in value.subjects)), 'future_availability')):
        with pytest.raises(ValueError, match=error):
            replace(value, **change)


def test_optional_missing_night_does_not_change_required_us_market_facts():
    parts = fixture('us')
    packet, seed, graph = parts
    for path, document in packet['publication_context'].items():
        projection = dict(contract='unified-class-c-owner-projection-v1',
            role=path.removeprefix('class-c/').removesuffix('.json'), eligible=False,
            records=[], version=digest([]), values=[], denials=[])
        projection['projection_sha256'] = digest(projection)
        document['projection'] = projection
    packet['authority_graph_sha256'] = digest(graph)
    before = project(deepcopy(parts))
    packet, seed, graph = parts
    night = night_fixture(case='empty')
    seed['run_acquisitions']['night'] = night['value_sha256']
    graph.update(night=night, run_seed_sha256=digest(seed))
    packet.update(night_and_publication_context=night, run_seed_sha256=digest(seed), authority_graph_sha256=digest(graph))
    after = project(parts)
    old, new = before['packet']['market_context'], after['packet']['market_context']
    assert not new['night_futures']
    assert new['optional_denials']['night_futures']['state'] == 'UNAVAILABLE_NO_CURRENT_FINAL_ROW'
    assert {k:v for k,v in old['coverage'].items() if k != 'night_futures'} == {k:v for k,v in new['coverage'].items() if k != 'night_futures'}
    assert old['fact_catalog'] == new['fact_catalog']
    assert after['receipt']['numeric_alias_binding']['status'] == 'PASS'


def test_integrated_import_and_old_calendar_default_keep_exact_modes():
    from app.services.unified_sealed_context import replay_night
    from app.services.price_structure_v3_renderer_service import render_current_price_structure
    assert callable(replay_night) and callable(render_current_price_structure)
    assert sealed_night_end_date_history({'observations':[]}) is False
    value = {'observations':[{'raw_payload':{'night_timeframes':{'calendar_contract':'KRX_NIGHT_END_DATE_V1'}}}]}
    assert sealed_night_end_date_history(value) is True
    value['observations'].append({'raw_payload':{'night_timeframes':{'calendar_contract':None}}})
    with pytest.raises(ValueError, match='mixed_or_unknown'):
        sealed_night_end_date_history(value)
    assert job.LOCAL_CAPS['us']['krx_night_futures'] == 7


def test_us0810_calendar_skips_closed_days_without_kr_schedule_change():
    assert target_session('us', DateTime.fromisoformat('2026-11-22T08:10:00+09:00')) is None
    assert target_session('us', DateTime.fromisoformat('2026-11-23T08:10:00+09:00')) is None
    assert str(target_session('us', DateTime.fromisoformat('2026-11-24T08:10:00+09:00'))) == '2026-11-23'
    assert target_session('kr', DateTime.fromisoformat('2026-11-21T15:35:00+09:00')) is None


def test_fixture_entry_permission_and_fixed_renderer_remain_separate():
    from scripts.m12da_source_use_contract import SourceUse, is_use_allowed
    from tests.test_m12da_source_use_contract import _projection
    from tests.test_price_structure_v3_renderer_service import _zone, _summary
    from app.services.price_structure_v3_renderer_service import render_current_price_structure
    projection = _projection()
    assert is_use_allowed(projection, ref_id='canonical:price', use=SourceUse.ENTRY)
    assert not is_use_allowed(projection, ref_id='source:working-capital', use=SourceUse.ENTRY)
    support = _zone('support', '98', '99', '$98~99')
    support['as_of'] = '2026-11-20'
    rendered = render_current_price_structure(_summary(support=support), ticker='TOY_ONLY',
        as_of='2026-11-20', current_price=100, currency='USD', include_current_price=False)
    assert rendered is not None


def test_c28_exact_tag_window_market_year_and_no_early_late_fire(tmp_path, monkeypatch):
    path, _ = configuration(tmp_path)
    monkeypatch.setattr(job, '_local_registered_cycle', lambda *a, **kw: pytest.fail('closed_must_not_start'))
    assert job.one_shot_scope('us', TAG) is False
    assert job._us_full_one_shot_window(TAG) == (START, START + timedelta(minutes=10))
    assert job._one_shot_deadline(TAG) == START + timedelta(hours=4, minutes=30)
    assert str(job.latest_one_shot_us_session(START, one_shot_tag=TAG)) == '2026-11-20'
    for at in (START-timedelta(seconds=1), START+timedelta(minutes=10), START.replace(year=2027)):
        clock(monkeypatch, at)
        assert asyncio.run(job.run_local_scheduled(path, 'us', now=at, one_shot_tag=TAG))['status'] == 'NO_RUN'
    for market, tag in (('kr',TAG), ('us',TAG+'a'), ('us','us-20271121-c28d7e1f')):
        with pytest.raises(ValueError, match='tag_scope_invalid'):
            job.one_shot_scope(market, tag)


def test_c28_single_consumption_retains_failure_and_existing_call_caps(tmp_path, monkeypatch):
    path, _ = configuration(tmp_path)
    code_pin(monkeypatch)
    clock(monkeypatch, START)
    calls = []
    async def cycle(*args, **kwargs):
        calls.append(kwargs['one_shot_tag'])
        raise RuntimeError('synthetic_failure_not_an_authorized_retry')
    monkeypatch.setattr(job, '_local_registered_cycle', cycle)
    with pytest.raises(RuntimeError):
        asyncio.run(job.run_local_scheduled(path, 'us', now=START, one_shot_tag=TAG))
    assert asyncio.run(job.run_local_scheduled(path, 'us', now=START, one_shot_tag=TAG))['reason'] == 'SESSION_ALREADY_CONSUMED'
    run = tmp_path / 'runs/one-shot/2026-11-21' / TAG
    intent = json.loads((run/'intent.json').read_bytes())
    assert (intent['max_http'], intent['max_models'], intent['source_seconds']) == (710,42,1800)
    assert intent['b2_retry_policy'] == job.B2_PER_TICKER_ONE_RETRY_V1
    assert len(calls) == 1 and (run/'terminal.json').exists()


def test_c28_shared_existing_lease_prevents_second_worker_before_intent(tmp_path, monkeypatch):
    path, _ = configuration(tmp_path)
    code_pin(monkeypatch)
    clock(monkeypatch, START)
    monkeypatch.setattr(job, '_local_registered_cycle', lambda *a, **kw: pytest.fail('busy_must_not_start'))
    with (tmp_path/'pair.lease').open('rb') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = asyncio.run(job.run_local_scheduled(path,'us',now=START,one_shot_tag=TAG))
    assert result['reason'] == 'NO_RUN_LOCK_BUSY'
    assert not list((tmp_path/'runs').rglob('intent.json'))
