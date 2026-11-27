import asyncio
import json
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.jobs import preopen_briefing as job
from app.services import preopen_briefing as briefing
from app.services.monitoring_summary import summary_message
from app.services.research_no_send_run import PARTIAL, TERMINAL
from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest


@pytest.mark.parametrize('market,at,expected', [
    ('kr', '2026-11-30T07:30:00+09:00', ('2026-11-30', '2026-11-27', '07:45', '07:50')),
    ('kr', '2026-07-03T07:30:00+09:00', ('2026-07-03', '2026-07-02', '07:45', '07:50')),
    ('kr', '2026-11-29T07:30:00+09:00', None),
    ('kr', '2026-11-30T07:50:00+09:00', None),
    ('us', '2026-11-30T22:30:00+09:00', ('2026-11-30', '2026-11-27', '08:55', '09:00')),
    ('us', '2026-11-30T21:30:00+09:00', None),
    ('us', '2026-07-06T21:30:00+09:00', ('2026-07-06', '2026-07-02', '08:55', '09:00')),
    ('us', '2026-07-06T22:30:00+09:00', None),
    ('us', '2026-07-03T21:30:00+09:00', None),
    ('us', '2026-11-26T08:30:00-05:00', None),
])
def test_exchange_holidays_and_dst_candidates(market, at, expected):
    slot = briefing.preopen_window(market, datetime.fromisoformat(at))
    if expected is None:
        assert slot is None
    else:
        assert (str(slot.opening_session), str(slot.base_session),
                slot.collection_end.strftime('%H:%M'), slot.delivery_end.strftime('%H:%M')) == expected


def test_earlier_special_open_shortens_window(monkeypatch):
    monkeypatch.setattr(briefing, 'exchange_session_open',
                        lambda *_: datetime.fromisoformat('2026-11-30T08:52:00-05:00'))
    slot = briefing.preopen_window('us', datetime.fromisoformat('2026-11-30T08:30:00-05:00'))
    assert slot.delivery_end.strftime('%H:%M') == '08:52'
    assert slot.collection_end.strftime('%H:%M') == '08:47'
    assert briefing.preopen_window('us', datetime.fromisoformat('2026-11-30T08:52:00-05:00')) is None


def _terminal(root, monkeypatch, *, completed, partial):
    from app.services import production_message_renderer as renderer
    from app.services.vnext_execution_profile import SOL_HIGH_V1
    from tests.test_c44_renderer_replay import synthetic_renderer_case

    session, ticker, accepted, result, _ = synthetic_renderer_case('us')
    generation = f'local-us-{completed}-consumer'
    cutoff = f'{completed}T17:10:00-05:00'
    monkeypatch.setattr(renderer, 'stock_plan', lambda *_: accepted)
    # The accepted fixture retains its own identifiers while rendering. Only
    # the terminal fixture below supplies the synthetic regular run identity.
    detail = renderer.stock_message(session, ticker, result, execution_profile=SOL_HIGH_V1, include_summary=True)
    detail.update(generation_id=generation, NO_SEND=True)
    omitted = {'ZZZ': {'status': 'B2_UNISSUED_TIMEOUT'}} if partial else {}
    subjects = [ticker, *omitted]
    market = dict(message_id='MARKET_US', text='기존 시장 판단', generation_id=generation,
                  plan_sha256=digest('market'), NO_SEND=True)
    summary = summary_message(market='us', generation=generation, subjects=subjects,
                              messages=[detail], omitted=omitted, completed=completed, cutoff=cutoff)
    summary['NO_SEND'] = True
    messages = [market, summary, detail]
    cycle = root / f'us-{completed}'
    terminal = dict(status=PARTIAL if partial else TERMINAL, messages=messages,
        messages_sha256=digest(messages), normal_messages_sent=False, failure_notifications_sent=False,
        child_binding=dict(run_id=generation, market='us', cutoff=cutoff,
                           source_generation=f'local-us-{completed}-source', include_summary=True,
                           message_ids=['MARKET_US', 'SUMMARY_US', *subjects]), unissued=omitted)
    durable_json(cycle / 'intent.json', dict(market='us', session=completed, code_commit='c' * 40))
    durable_json(cycle / 'terminal.json', terminal)
    return cycle, messages


@pytest.mark.parametrize('partial,mode', [(False, 'offline'), (True, 'busy'), (True, 'timeout')])
def test_scheduled_run_keeps_actual_producer_originals_and_source_failure_fallback(tmp_path, monkeypatch, partial, mode):
    run_roots = {'us': tmp_path / 'us', 'kr': tmp_path / 'kr'}
    cycle, originals = _terminal(run_roots['us'], monkeypatch, completed='2026-11-23', partial=partial)
    before = (cycle / 'terminal.json').read_bytes()
    preview_root = tmp_path / 'preview'
    lease = tmp_path / 'existing.lock'
    lease.touch()
    calls = []

    async def sources(_market, *, enable_network, **_):
        calls.append(enable_network)
        if enable_network:
            raise TimeoutError
        return {'market': [], 'events': {}, 'coverage': []}

    monkeypatch.setattr(job, 'collect_preopen_sources', sources)
    def now():
        return datetime.fromisoformat('2026-11-24T08:30:00-05:00')

    args = dict(run_roots=run_roots, preview_root=preview_root, clock=now,
                collect=mode != 'offline', shared_lease_path=lease)
    if mode == 'busy':
        with job._local_lock(lease, existing=True):
            result = asyncio.run(job.run_preopen('us', **args))
    else:
        result = asyncio.run(job.run_preopen('us', **args))
    assert result['mode'] == 'NO_SEND' and result['status'] == 'COMPLETE'
    assert result['normal_messages_sent'] is False
    preview = json.loads(Path(result['preview_path']).read_text())
    assert preview['metadata']['model_calls'] == 0
    assert preview['metadata']['base_status'] == ('PARTIAL' if partial else 'COMPLETE')
    assert len(preview['messages']) == 3
    assert before == (cycle / 'terminal.json').read_bytes()
    for message, original in zip(preview['messages'], originals, strict=True):
        assert message['message_id'] == original['message_id']
        assert original['text'] in message['text']
        assert message['base_content_sha256'] == digest(original['text'])
    if partial:
        assert 'ZZZ · B2 타임아웃' in preview['messages'][1]['text']
        assert preview['metadata']['source_coverage'][-1]['status'] == (
            'LOCK_BUSY' if mode == 'busy' else 'TIMEOUT')
    assert calls == ([True, False] if mode == 'timeout' else [False])
    assert asyncio.run(job.run_preopen('us', **args))['duplicate'] is True
    assert calls == ([True, False] if mode == 'timeout' else [False])


def test_render_eligible_quote_keeps_price_and_observation_scope(monkeypatch):
    from decimal import Decimal

    from app.services.preopen_applicability import Applicability, PriceComparison

    now = datetime.fromisoformat('2026-11-30T08:35:00-05:00')
    price = PriceComparison('RR_AVAILABLE', value=Decimal('55.21'), currency='USD',
        observed_at=now, source='fixture', latency_seconds=Decimal('5'), close_change_pct=Decimal('0.21'),
        reference_rr=Decimal('2.12'), scenario='SUPPORT', rr_at_least_two=True,
        preference_relation='AT_OR_BELOW', preference_conditional=True)
    monkeypatch.setattr(briefing, 'assess_stock', lambda *_a, **_kw:
                        Applicability('조건 확인', '조건부 검토', price, 'CONFIRMED_CONDITIONAL'))
    base = SimpleNamespace(status='COMPLETE', is_current=True, cutoff=None, session=date(2026, 11, 27),
                           messages=(), rows=[dict(ticker='AAA', status='COMPLETE', economic='ATTRACTIVE')])
    result = briefing.render_briefing('us', briefing.preopen_window('us', now), base,
                                     dict(market=[], events={}, coverage=[]), now)
    summary = result[1]['text']
    assert '55.21 USD' in summary and '08:35:00 ET · fixture · 지연 5초' in summary
    assert '선택 지지 시나리오 참고 RR 2.12배' in summary and '경제적 선호가 이내(조건부)' in summary
