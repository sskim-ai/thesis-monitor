"""Read the regular NO_SEND result without reopening Source or model plans."""
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from app.services.market_session import is_exchange_session_date
from app.services.monitoring_summary import verify_summary_message
from app.services.research_artifact_budget import plain_path
from app.services.research_no_send_run import PARTIAL, TERMINAL
from app.services.unified_run_artifacts import load_json
from app.services.unified_snapshot_contract import digest

EXCHANGES = {'kr': 'XKRX', 'us': 'XNYS'}
ACCEPTED = {TERMINAL: 'COMPLETE', PARTIAL: 'PARTIAL'}
OMISSIONS = {'CORE_UNISSUED_TIMEOUT', 'A_UNISSUED_TIMEOUT',
             'B_UNISSUED_TIMEOUT', 'B2_UNISSUED_TIMEOUT'}


@dataclass(frozen=True)
class PreopenBase:
    expected_session: date
    status: str
    session: date | None = None
    messages: tuple[dict, ...] = ()
    rows: tuple[dict, ...] = ()
    cutoff: datetime | None = None
    completed_at: datetime | None = None
    generation_id: str | None = None
    messages_sha256: str | None = None
    source_generation_id: str | None = None
    subjects: tuple[str, ...] = ()
    code_commit: str | None = None

    @property
    def is_current(self):
        return self.session == self.expected_session and self.status in ACCEPTED.values()


def _timestamp(value):
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError('preopen_base_unzoned_timestamp')
    return result


def _regular_result(directory, market, session):
    """Only the outer terminal establishes that the scheduled cycle finished."""
    try:
        terminal = plain_path(directory / 'terminal.json')
        intent_path = plain_path(directory / 'intent.json')
        if not terminal.exists():
            return ('FAILED' if (directory / 'STOP').exists() else
                    'IN_PROGRESS' if intent_path.exists() else 'MISSING'), {}
        result = load_json(terminal)
        status = result['status']
        intent = load_json(intent_path)
        if (intent['market'], intent['session']) != (market, session.isoformat()) or 'one_shot_tag' in intent:
            return 'CORRUPT', {}
        if status in {'FAILED_NO_SEND', 'STOPPED_NO_SEND', 'STOPPED', 'FAILED'}:
            return 'FAILED', {}
        if status not in ACCEPTED:
            return 'CORRUPT', {}
        return ACCEPTED[status], _verified(result, intent, market, session)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError):
        return 'CORRUPT', {}


def _verified(result, intent, market, session):
    binding = result['child_binding']
    run = f'local-{market}-{session.isoformat()}'
    cutoff = _timestamp(binding['cutoff'])
    finished = _timestamp(result['completed_at']) if result.get('completed_at') is not None else None
    source_gen, generation = binding['source_generation'], binding['run_id']
    expected = binding['message_ids']
    messages = result['messages']
    omitted = result.get('unissued', {})
    market_id, summary_id = f'MARKET_{market.upper()}', f'SUMMARY_{market.upper()}'
    has_summary = binding.get('include_summary') is True
    headers = [market_id, summary_id] if has_summary else [market_id]
    subjects = tuple(expected[len(headers):])
    if (binding['market'] != market or generation != run + '-consumer' or source_gen != run + '-source'
            or (finished is not None and finished < cutoff)
            or result['normal_messages_sent'] is not False
            or result['failure_notifications_sent'] is not False
            or expected[:len(headers)] != headers or set(headers) & set(subjects)
            or len(set(subjects)) != len(subjects) or not subjects
            or bool(omitted) != (result['status'] == PARTIAL) or set(omitted) - set(subjects)
            or any(r['status'] not in OMISSIONS for r in omitted.values())
            or [m['message_id'] for m in messages] != [m for m in expected if m not in omitted]
            or digest(messages) != result['messages_sha256']
            or any(m['NO_SEND'] is not True or m['generation_id'] != generation
                   or not isinstance(m['text'], str) or not m['text'] or not m['plan_sha256']
                   for m in messages)):
        raise ValueError('preopen_base_terminal_binding_drift')
    if has_summary:
        verify_summary_message(messages=messages, market=market, subjects=subjects, omitted=omitted,
            expected_cutoff=binding['cutoff'], expected_generation=generation,
            expected_completed=session.isoformat())
        rows = tuple(_eligible_projection(row, market, session) for row in messages[1]['summary_binding']['rows'])
    else:
        # Only structured identities and dispositions survive in pre-Summary terminals.
        emitted = {m['message_id']: m for m in messages}
        rows = tuple(dict(ticker=ticker, status=(omitted[ticker]['status'] if ticker in omitted else
            'UNKNOWN_LIMIT' if emitted[ticker].get('decision_mode') == 'UNKNOWN_LIMIT' else 'LEGACY'))
            for ticker in subjects)
    limits = set(binding.get('limitation_subjects', ())) - set(omitted)
    if limits != {row['ticker'] for row in rows if row['status'] == 'UNKNOWN_LIMIT'}:
        raise ValueError('preopen_base_limitation_binding_drift')
    return dict(session=session, messages=tuple(messages), rows=rows, cutoff=cutoff,
        completed_at=finished, generation_id=generation, messages_sha256=result['messages_sha256'],
        source_generation_id=source_gen, subjects=subjects, code_commit=intent['code_commit'])


def _eligible_projection(row, market, session):
    """A bad optional stock projection cannot replace the verified original row."""
    preopen = row.get('preopen')
    if preopen is None:
        return row
    if isinstance(preopen, dict):
        security = preopen.get('security')
        if (preopen.get('market') == market and preopen.get('close_session') in (None, session.isoformat())
                and (security is None or isinstance(security, dict) and security.get('ticker') == row['ticker']
                     and security.get('canonical_security_id') == preopen.get('security_id'))):
            return row
    return {key: value for key, value in row.items() if key != 'preopen'}


def read_preopen_base(run_root: Path, market: str, base_session: date, *, allow_reference=True) -> PreopenBase:
    root = plain_path(run_root)
    prefix = market + '-'
    status, result = _regular_result(root / (prefix + base_session.isoformat()), market, base_session)
    if result or not allow_reference:
        return PreopenBase(base_session, status, **result)
    older = []
    for path in root.glob(prefix + '????-??-??'):
        key = path.name.removeprefix(prefix)
        try:
            day = date.fromisoformat(key)
        except ValueError:
            continue
        if day < base_session and day.isoformat() == key:
            older.append(day)
    for day in sorted(older, reverse=True):
        if is_exchange_session_date(EXCHANGES[market], day):
            _, result = _regular_result(root / (prefix + day.isoformat()), market, day)
            if result:
                return PreopenBase(base_session, status, **result)
    return PreopenBase(base_session, status)
