from datetime import date

import pytest

from app.services.monitoring_summary import summary_message
from app.services.preopen_base import read_preopen_base
from app.services.research_no_send_run import PARTIAL, TERMINAL
from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest


def _terminal(root, *, market, session, details=(), omitted=None, include_summary=True, status=None):
    omitted = omitted or {}
    generation = f'local-{market}-{session}'
    directory = root / f'{market}-{session}'
    durable_json(directory / 'intent.json', dict(market=market, session=session, code_commit='base-commit'))
    if status:
        durable_json(directory / 'terminal.json', dict(status=status))
        return directory
    ids = [m['message_id'] for m in details]
    details = [dict(m, generation_id=generation+'-consumer') for m in details]
    subjects = [*ids, *omitted]
    cutoff = f'{session}T23:10:00+00:00'
    messages = [dict(message_id=f'MARKET_{market.upper()}', text='장 마감 원문', plan_sha256='market')]
    if include_summary:
        messages.append(summary_message(market=market, generation=generation+'-consumer', subjects=subjects,
            messages=details, omitted=omitted, completed=session, cutoff=cutoff))
    messages.extend(details)
    messages = [dict(m, NO_SEND=True, generation_id=generation+'-consumer') for m in messages]
    terminal = dict(status=PARTIAL if omitted else TERMINAL, messages=messages, messages_sha256=digest(messages),
        normal_messages_sent=False, failure_notifications_sent=False, unissued=omitted,
        **(dict(completed_at=f'{session}T23:20:00+00:00') if include_summary else {}),
        child_binding=dict(market=market, run_id=generation+'-consumer', source_generation=generation+'-source',
            cutoff=cutoff, include_summary=include_summary, message_ids=[*(m['message_id'] for m in messages), *omitted]))
    durable_json(directory / 'terminal.json', terminal)
    return directory, terminal


@pytest.mark.parametrize('market,partial', [('kr', False), ('us', True)])
def test_accepted_numeric_detail_through_existing_summary_and_terminal(market, partial, tmp_path, monkeypatch):
    from app.services import production_message_renderer as renderer
    from app.services.vnext_execution_profile import SOL_HIGH_V1
    from tests.test_c44_renderer_replay import synthetic_renderer_case

    session, ticker, accepted, result, _ = synthetic_renderer_case(market, include_support=True)
    monkeypatch.setattr(renderer, 'stock_plan', lambda *_: accepted)
    detail = renderer.stock_message(session, ticker, result, execution_profile=SOL_HIGH_V1, include_summary=True)
    omitted = {'NEXT': dict(status='B2_UNISSUED_TIMEOUT')} if partial else {}
    _, original = _terminal(tmp_path, market=market, session='2026-11-23', details=[detail], omitted=omitted)

    read = read_preopen_base(tmp_path, market, date(2026, 11, 23))
    assert read.is_current and read.status == ('PARTIAL' if partial else 'COMPLETE')
    assert read.messages == tuple(original['messages']) and read.messages_sha256 == digest(original['messages'])
    assert read.completed_at > read.cutoff
    assert read.rows[0] == detail['summary_row']
    numeric = read.rows[0]['preopen']
    assert numeric['close'] == 10 and numeric['price_basis'] == 'adjusted_close'
    assert numeric['support']['low'] == 9 and numeric['support']['high'] == 11
    assert numeric['current_scenario'] is None and numeric['entry_quality'] == read.rows[0]['entry_quality']
    if partial:
        assert read.rows[1]['status'] == 'B2_UNISSUED_TIMEOUT'

    # A stale optional price payload loses its applicability, within the one stock.
    detail['summary_row']['preopen']['close_session'] = '2026-11-20'
    _, stale = _terminal(tmp_path, market=market, session='2026-11-23', details=[detail], omitted=omitted)
    read = read_preopen_base(tmp_path, market, date(2026, 11, 23))
    assert read.is_current and read.messages == tuple(stale['messages']) and 'preopen' not in read.rows[0]
    assert stale['messages'][1]['text'] == original['messages'][1]['text']


def test_legacy_reference_uses_prior_regular_result_and_keeps_latest_failure(tmp_path):
    day = date(2026, 11, 27)
    detail = dict(message_id='AAA', text='이전 상세 원문', plan_sha256='legacy')
    directory, _ = _terminal(tmp_path, market='us', session='2026-11-25', details=[detail], include_summary=False)
    one_shot = tmp_path / 'one-shot' / '2026-11-27' / directory.name
    durable_json(one_shot / 'terminal.json', {'status': TERMINAL})
    _terminal(tmp_path, market='us', session=day.isoformat(), status='STOPPED_NO_SEND')

    read = read_preopen_base(tmp_path, 'us', day)
    assert read.status == 'FAILED' and not read.is_current and read.session == date(2026, 11, 25)
    assert read.rows == ({'ticker': 'AAA', 'status': 'LEGACY'},)
    assert read.messages[-1]['text'] == detail['text'] and read.completed_at is None
    exact = read_preopen_base(tmp_path, 'us', day, allow_reference=False)
    assert exact.status == 'FAILED' and not exact.messages and exact.session is None


def test_running_and_corrupt_terminal_stay_distinct(tmp_path):
    day = date(2026, 11, 27)
    assert read_preopen_base(tmp_path, 'kr', day).status == 'MISSING'
    directory = tmp_path / f'kr-{day}'
    durable_json(directory / 'intent.json', dict(market='kr', session=str(day)))
    assert read_preopen_base(tmp_path, 'kr', day).status == 'IN_PROGRESS'
    detail = dict(message_id='AAA', text='기존 상세 원문', plan_sha256='legacy')
    _, original = _terminal(tmp_path, market='kr', session=str(day), details=[detail], include_summary=False)
    original['messages'][-1]['text'] = '변경된 상세 원문'
    durable_json(directory / 'terminal.json', original)
    assert read_preopen_base(tmp_path, 'kr', day).status == 'CORRUPT'


def test_news_and_official_use_actual_receipt_times_and_existing_ids():
    from app.services.fresh_financial_stock_owner import _preopen_source
    from app.services.monitoring_summary import preopen_source_context

    before, after = '2026-11-27T08:20:00+09:00', '2026-11-27T08:20:02+09:00'
    plan = dict(security=dict(ticker='AAA', cik='0000001000'), provider='sec_edgar',
        cutoff='2026-11-27T08:10:00+09:00')
    capture = _preopen_source(plan, dict(selected_filings=[dict(accessionNumber='123-26-000001')]),
        [dict(stage='discovery', started_at=before, finished_at=after)])
    source = dict(preopen_source=capture, event_view=dict(
        receipt=dict(request_started_at=before, received_at=after, source_query_cutoff=after),
        binding=dict(provider='google_news_rss', denial=None,
                     selected=[dict(event_fingerprint='considered', status='PASS'),
                               dict(event_fingerprint='later_release', status='DENIED')])))
    watermarks = preopen_source_context(source)['event_watermarks']
    assert watermarks['sec_edgar']['requested_at'] == before
    assert watermarks['sec_edgar']['source_query_cutoff'] != before
    assert watermarks['sec_edgar']['ids'] == ['123-26-000001']
    assert watermarks['google_news_rss']['status'] == 'CHECKED'
    assert watermarks['google_news_rss']['ids'] == ['considered']
