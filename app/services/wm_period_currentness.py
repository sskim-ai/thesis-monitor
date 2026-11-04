"""Calendar-aware W/M source diagnostics; provider semantics require review.

Calendar consistency is not provider label authority. No production label spec
has been established by the retained Kiwoom adapter or captured rows yet.
"""
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from types import MappingProxyType
from zoneinfo import ZoneInfo

from app.services.market_session import exchange_calendar
from app.services.unified_snapshot_contract import digest

CONTRACT = 'wm-period-currentness-v1'


@dataclass(frozen=True)
class _LabelSpec:
    basis: str
    source_field: str
    official_document_sha256: str
    parser_sha256: str


# Only an independently reviewed provider/document/parser contract may populate
# this code-pinned registry. Caller flags, raw patterns and hashes cannot do so.
_LABEL_CONTRACTS = MappingProxyType({})
_VENUES = {'kr': {'KRX', 'KOSPI', 'KOSDAQ'}, 'us': {'ND', 'NY', 'NA'}}


def _require(value, message):
    if not value:
        raise ValueError(message)


def _date(value):
    result = date.fromisoformat(value)
    _require(result.isoformat() == value, 'wm_date_not_canonical')
    return result


def _calendar(read, first_label, target):
    _require(read.market in _VENUES and read.exchange in _VENUES[read.market],
             'wm_exchange_mismatch')
    _require(0 <= (target - first_label).days <= 36600, 'wm_calendar_range_unbounded')
    return exchange_calendar.get_calendar('XKRX' if read.market == 'kr' else 'XNYS',
        start=first_label.replace(day=1) - timedelta(days=7),
        end=target.replace(day=monthrange(target.year, target.month)[1]) + timedelta(days=7))


def _bounds(calendar, label, timeframe):
    if timeframe == 'weekly':
        start = label - timedelta(days=label.weekday())
        end = start + timedelta(days=6)
    else:
        start = label.replace(day=1)
        end = label.replace(day=monthrange(label.year, label.month)[1])
    # No weekday approximation or calendar-range fallback.
    sessions = calendar.sessions_in_range(start, end)
    _require(len(sessions) > 0, 'wm_period_has_no_sessions')
    return start, end, sessions[0].date(), sessions[-1].date()


def period_view(rows, *, read, observed_at, cutoff, label_basis='UNKNOWN'):
    """Hypothesis-only classification, never an Owner or technical permission.

    Even a caller-specified basis can only produce a diagnostic, not admission.
    Closed counts are unknown unless a basis is explicitly being hypothesized.
    """
    _require(read.timeframe in {'weekly', 'monthly'}, 'wm_timeframe_required')
    _require(observed_at.utcoffset() is not None and cutoff.utcoffset() is not None
             and observed_at >= cutoff, 'wm_observation_time_invalid')
    target = _date(read.latest_completed_session)
    labels = [_date(row['date']) for row in rows]
    _require(len(labels) >= read.count and labels == sorted(set(labels)), 'wm_history_or_label_order_invalid')
    calendar = _calendar(read, labels[0], target)
    local = observed_at.astimezone(ZoneInfo('Asia/Seoul' if read.market == 'kr' else 'America/New_York'))
    session = calendar.date_to_session(local.date(), direction='previous')
    if calendar.session_close(session).to_pydatetime() > observed_at:
        session = calendar.previous_session(session)
    _require(session.date() == target and calendar.is_session(target), 'wm_completed_daily_session_mismatch')
    _require(labels[-1] <= target, 'wm_future_label')
    target_bounds = _bounds(calendar, target, read.timeframe)
    _require(_bounds(calendar, labels[-1], read.timeframe)[:2] == target_bounds[:2], 'wm_stale_latest_period')
    _require(label_basis in {'UNKNOWN', 'FIRST_TRADING_SESSION', 'LAST_TRADING_SESSION', 'SESSION_DATE'},
             'wm_label_basis_unknown')
    states = []
    for label in labels:
        start, end, first, last = _bounds(calendar, label, read.timeframe)
        if label_basis != 'UNKNOWN':
            expected = first if label_basis == 'FIRST_TRADING_SESSION' else last
            _require(calendar.is_session(label) and (label_basis == 'SESSION_DATE' or label == expected),
                     'wm_provider_label_basis_mismatch')
        closed = last <= target and calendar.session_close(last).to_pydatetime() <= observed_at
        states.append('CLOSED_PERIOD' if closed else 'PROVISIONAL_ACTIVE_PERIOD')
    proven_counts = label_basis != 'UNKNOWN'
    return dict(contract=CONTRACT, status='DIAGNOSTIC_NOT_PROVIDER_AUTHORITY',
        calendar=calendar.name, timezone=local.tzinfo.key, target_session=target.isoformat(),
        observed_at=observed_at.isoformat(), cutoff=cutoff.isoformat(),
        label_basis=label_basis, label_basis_proven=False,
        period_start=target_bounds[0].isoformat(), period_end=target_bounds[1].isoformat(),
        first_trading_session=target_bounds[2].isoformat(), last_trading_session=target_bounds[3].isoformat(),
        last_source_label=labels[-1].isoformat(), raw_rows=len(rows),
        latest_calendar_state=states[-1],
        hypothetical_closed_rows=states.count('CLOSED_PERIOD') if proven_counts else None,
        hypothetical_provisional_rows=states.count('PROVISIONAL_ACTIVE_PERIOD') if proven_counts else None,
        completed_only_requires_excluding_provisional=True,
        source_only_eligible=False, technical_signal=False, native_use=False, date_relabel_count=0)


def source_period_proof(rows, *, read, receipt, original_proof, cutoff, parser_pins):
    """Supplement original live replay; never replace its false daily alignment.

    The original Parent/dispatcher/custody validation remains the caller's first
    prerequisite. This helper accepts no review flag or caller label contract.
    """
    _require(original_proof['status'] == 'ORIGINAL_SOURCE_ROLE_REPLAY_PASS'
             and original_proof['two_original_owner_replays'] == 'PASS'
             and original_proof['original_role_validation']['status'] == 'PASS'
             and original_proof['original_window_validation']['status'] == 'PASS'
             and original_proof['requested_count_reached'] is True, 'wm_original_replay_required')
    _require(receipt['entry'] == read.model_dump(mode='json') and receipt['status'] == 'CAPTURED'
             and receipt['pages'] and digest(rows) == receipt['normalized_sha256'], 'wm_original_source_binding')
    for page in receipt['pages']:
        _require(page['entry_id'] == read.entry_id and page['provider'] == read.provider
                 and len(page['source_sha256']) == 64, 'wm_original_page_binding')
    observed = datetime.fromisoformat(receipt['completed_at'])
    diagnostic = period_view(rows, read=read, observed_at=observed, cutoff=cutoff)
    spec = _LABEL_CONTRACTS.get((read.provider, read.api_id, read.timeframe))
    _require(isinstance(spec, _LabelSpec), 'wm_provider_label_semantics_unverified')
    _require(spec.basis in {'FIRST_TRADING_SESSION', 'LAST_TRADING_SESSION'}
             and len(spec.official_document_sha256) == 64 and spec.source_field
             and parser_pins.get('app/providers/kiwoom.py', {}).get('sha256') == spec.parser_sha256,
             'wm_reviewed_label_parser_binding_required')
    classified = period_view(rows, read=read, observed_at=observed, cutoff=cutoff, label_basis=spec.basis)
    return dict(contract=CONTRACT, scope='SCOPED_SOURCE_ONLY',
        classification=classified, label_basis_proven=True,
        official_document_sha256=spec.official_document_sha256, source_field=spec.source_field,
        parser_sha256=spec.parser_sha256, source_receipt_sha256=digest(receipt),
        normalized_sha256=receipt['normalized_sha256'], raw_sha256=[p['source_sha256'] for p in receipt['pages']],
        original_role_proof_sha256=digest(original_proof),
        original_current_session_aligned=original_proof['original_role_validation']['current_session_aligned'],
        original_generation=receipt['run_id'], acquisition_id=receipt['acquisition_id'],
        security_id=read.canonical_security_id, diagnostic_sha256=digest(diagnostic),
        technical_signal=False, completed_price_authority=False, financial_use=False,
        valuation_use=False, economic_use=False, native_use=False, model_use=False)


def capture_period_proof(rows, *, read, receipt, original_proof, cutoff, parser_pins):
    """Capture integrity survives unknown labels, but current-use does not.

    Only the original live issuer calls this after custody/replay qualification.
    The strict classified path above remains available and fail-closed.
    """
    try:
        classified = source_period_proof(rows, read=read, receipt=receipt,
            original_proof=original_proof, cutoff=cutoff, parser_pins=parser_pins)
    except ValueError as exc:
        if str(exc) != 'wm_provider_label_semantics_unverified':
            raise
        return dict(contract='wm-capture-evidence-v2', state='SOURCE_ONLY_HISTORICAL_OR_PROVISIONAL',
            label_basis='UNKNOWN', label_basis_proven=False, completed_rows=None,
            provisional_rows=None, current_source_authority=False,
            original_current_session_aligned=original_proof['original_role_validation']['current_session_aligned'],
            diagnostic=period_view(rows, read=read, observed_at=datetime.fromisoformat(receipt['completed_at']), cutoff=cutoff),
            source_receipt_sha256=digest(receipt), normalized_sha256=receipt['normalized_sha256'],
            original_role_proof_sha256=digest(original_proof),
            raw_sha256=[p['source_sha256'] for p in receipt['pages']],
            original_generation=receipt['run_id'], acquisition_id=receipt['acquisition_id'],
            security_id=read.canonical_security_id, technical_signal=False,
            completed_price_authority=False, financial_use=False, valuation_use=False,
            economic_use=False, native_use=False, model_use=False)
    return dict(classified, state='PERIOD_CLASSIFIED_SOURCE_ONLY', current_source_authority=False)


def pure_parser(external_root, pins):
    """Original pinned normalization methods only; no Provider or Settings boot."""
    import ast
    import hashlib
    from pathlib import Path
    from typing import Any

    root = Path(external_root)
    _require(root.is_absolute() and not any(p.is_symlink() for p in (root, *root.parents)), 'wm_parser_root')
    source = {}
    for name in ('app/providers/kiwoom.py', 'app/parsing.py'):
        path = root / name
        _require(not any(p.is_symlink() for p in (path, *path.parents)), 'wm_parser_symlink')
        raw = path.read_bytes()
        _require(dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()) == pins[name], 'wm_parser_pin')
        source[name] = raw
    scope = {'Any': Any}
    exec(compile(source['app/parsing.py'], str(root/'app/parsing.py'), 'exec'), scope)
    original = next(n for n in ast.parse(source['app/providers/kiwoom.py']).body
                    if isinstance(n, ast.ClassDef) and n.name == 'KiwoomProvider')
    methods = {'_normalize_rows', '_find_rows', '_pick', '_normalize_date', '_to_number'}
    nodes = [n for n in original.body if (isinstance(n, ast.FunctionDef) and n.name in methods)
             or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '_FIELD_KEYS' for t in n.targets))]
    tree = ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='PinnedPureParser', bases=[],
        keywords=[], body=nodes, decorator_list=[])], type_ignores=[]))
    exec(compile(tree, str(root/'app/providers/kiwoom.py'), 'exec'), scope)
    return scope['PinnedPureParser']()


def observed_label_examples(daily_rows, period_rows, *, read, daily_entry, daily_observed_at, period_observed_at):
    """Exact historical examples, not an official/global/current-use contract."""
    from decimal import Decimal
    _require(daily_entry['market'] == read.market and daily_entry['exchange'] == read.exchange
        and daily_entry['canonical_security_id'] == read.canonical_security_id
        and daily_entry['provider'] == read.provider and daily_entry['adjusted'] == read.adjusted
        and daily_entry['latest_completed_session'] == read.latest_completed_session
        and daily_entry['timeframe'] == 'daily', 'wm_daily_comparison_identity')
    target = _date(read.latest_completed_session)
    calendar = _calendar(read, _date(daily_rows[0]['date']), target)
    index = {r['date']: r for r in daily_rows}
    _require(len(index) == len(daily_rows), 'wm_daily_comparison_duplicates')
    examples = []
    for bar in reversed(period_rows):
        label = _date(bar['date']);start,end,first,last = _bounds(calendar, label, read.timeframe)
        if last >= target or first < _date(daily_rows[0]['date']):
            continue
        sessions = [s.date().isoformat() for s in calendar.sessions_in_range(start,end)]
        if not all(s in index for s in sessions):
            continue
        days = [index[s] for s in sessions]
        numeric = lambda value: Decimal(str(value))
        expected = dict(open=numeric(days[0]['open']), high=max(numeric(r['high']) for r in days),
            low=min(numeric(r['low']) for r in days), close=numeric(days[-1]['close']),
            volume=sum((numeric(r['volume']) for r in days), Decimal(0)))
        differences = {key: numeric(bar[key]) - value for key,value in expected.items()}
        examples.append(dict(label=label.isoformat(), first=first.isoformat(),last=last.isoformat(),
            sessions=len(sessions),first_session_label=label==first,
            exact_fields={key:value==0 for key,value in differences.items()},
            # Fractions only, no absolute price/volume values in review artifacts.
            relative_differences={key:str(value/abs(expected[key])) if expected[key] else ('0' if value==0 else 'UNDEFINED')
                                  for key,value in differences.items()}))
        if len(examples)==3:
            break
    passed = len(examples)==3 and all(e['first_session_label'] and all(e['exact_fields'].values()) for e in examples)
    return dict(contract='observed-provider-label-examples-v1', api_id=read.api_id, market=read.market,
        exchange=read.exchange, adjusted=read.adjusted, examples=examples,
        status='OBSERVED_EXACT_HISTORICAL_EXAMPLES' if passed else 'INCONCLUSIVE_OR_MISMATCH',
        scope='ONLY_THREE_TESTED_HISTORICAL_PERIODS_NOT_GLOBAL_SEMANTICS',
        daily_observed_at=daily_observed_at,period_observed_at=period_observed_at,
        same_capture_generation=False,official=False,current_period_finality='UNPROVEN',
        tolerance=0,current_source_authority=False)


def validate_period_readback(receipt, *, read, rows, stocks_root, external_root, sealed_raw, expected_parser_pins):
    """Recompute v2 evidence without recreating its retired live capability."""
    import json
    from types import SimpleNamespace
    from app.services.unified_stock_acquisition import validate_role, bound_artifact
    from app.services.sealed_native_bridge import require_complete_stock_window

    evidence = receipt['period_evidence']; original = evidence['source_receipt']
    _require(evidence['parser_pins']==expected_parser_pins, 'wm_cold_external_parser_contract')
    plan_value = evidence['stock_plan']
    plan = SimpleNamespace(run_id=plan_value['run_id'], acquisition_id=plan_value['acquisition_id'],
        frozen_at=datetime.fromisoformat(plan_value['frozen_at']), model_dump=lambda **_:plan_value)
    _require(original['entry'] == read.model_dump(mode='json')
        and receipt['generation_id'] == original['run_id'] == plan.run_id
        and receipt['acquisition_id'] == original['acquisition_id'] == plan.acquisition_id
        and receipt['stock_plan_sha256'] == digest(plan_value)
        and receipt['source_receipt_sha256'] == digest(original)
        and receipt['raw_sha256'] == [p['source_sha256'] for p in original['pages']]
        and receipt['observed_at'] == original['completed_at']
        and receipt['normalized_sha256'] == original['normalized_sha256'] == digest(rows), 'wm_cold_source_identity')
    _require(evidence['cutoff'] == plan_value['frozen_at'], 'wm_cold_cutoff')
    validation = validate_role(plan,read,original,stocks_root)
    window = require_complete_stock_window(read,original,rows)
    proof = evidence['original_proof']
    _require(validation == proof['original_role_validation'] and window == proof['original_window_validation']
        and receipt['proof_sha256'] == digest(proof), 'wm_cold_original_quality')
    parser = pure_parser(external_root,expected_parser_pins)
    keys = ['result_list','output','data'] if read.market=='us' else [
        'stk_stk_pole_chart_qry' if read.timeframe=='weekly' else 'stk_mth_pole_chart_qry','output','data']
    all_rows=[]
    for page in original['pages']:
        raw = bound_artifact(stocks_root,page['artifact'],page['source_sha256'])
        _require(raw == sealed_raw(page['source_sha256']), 'wm_cold_sealed_raw_mismatch')
        all_rows.extend(parser._find_rows(json.loads(raw),keys))
    _require(parser._normalize_rows(all_rows,read.count)==rows, 'wm_cold_original_parser_replay')
    replays=evidence['replays']
    _require(len(replays)==2 and replays[0]==replays[1], 'wm_cold_two_replays')
    for replay in replays:
        matches=[r for r in replay if r['entry_id']==read.entry_id]
        _require(len(matches)==1 and matches[0]['status']=='PASS'
            and matches[0]['normalized_sha256']==digest(rows) and matches[0]['network_calls']==0,
            'wm_cold_original_replay_binding')
    expected=capture_period_proof(rows,read=read,receipt=original,original_proof=proof,
        cutoff=plan.frozen_at,parser_pins=evidence['parser_pins'])
    _require(receipt['period_proof']==expected and receipt['current_source_authority'] is False
        and receipt['source_evidence_state']==expected['state'], 'wm_cold_period_recomputed_mismatch')
    return dict(status='WM_SOURCE_ONLY_EVIDENCE_RECOMPUTED',state=expected['state'],
        classified=expected.get('label_basis_proven',False),current_source_authority=False)
