"""Contiguous, dated research views. Raw receipts and strict roles are unchanged."""
from copy import deepcopy
from datetime import date, timedelta
import calendar
import json
import math

from app.services.price_structure_wave_fibonacci_v3_service import _calendar_for_range
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows, canonical_fingerprint
from app.services.ohlcv_feature_engine_service import build_multi_timeframe_feature_packet
from app.services.vnext_research_store import digest

CONTRACT = 'independent-contiguous-timeframe-research-v1'
DATED_DIAGNOSTIC_CONTRACT = 'terminal-anomaly-dated-diagnostic-v1'
APIS = {'KR': {'daily': 'ka10081', 'weekly': 'ka10082', 'monthly': 'ka10083'},
        'US': {'daily': 'usa06012', 'weekly': 'usa06013', 'monthly': 'usa06014'}}


def bounds(day, timeframe):
    if timeframe == 'daily':
        return day, day
    if timeframe == 'weekly':
        start = day - timedelta(days=day.weekday())
        return start, start + timedelta(days=4)
    if timeframe == 'monthly':
        return day.replace(day=1), day.replace(day=calendar.monthrange(day.year, day.month)[1])
    raise ValueError('timeframe_not_supported')


def analytic_view(rows, *, timeframe, market, session, source_kind='NATIVE',
                  basis='adjusted_close', daily_parent=None, lagged_end_policy=None,
                  terminal_evidence=None, calendar_policy=None):
    """Pure projection, not an authority issuer. Never stitch across a bad bar."""
    if lagged_end_policy is not None:
        if calendar_policy is not None:
            raise ValueError('legacy_diagnostic_calendar_policy_unsupported')
        return _lagged_diagnostic(rows, timeframe=timeframe, market=market, session=session,
            source_kind=source_kind, basis=basis, daily_parent=daily_parent,
            policy=lagged_end_policy, evidence=terminal_evidence)
    if market not in APIS or timeframe not in APIS[market] or basis != 'adjusted_close':
        raise ValueError('timeframe_basis_or_market')
    if source_kind not in ('NATIVE', 'DERIVED_FROM_DAILY'):
        raise ValueError('timeframe_source_kind')
    if source_kind == 'DERIVED_FROM_DAILY' and (timeframe == 'daily' or daily_parent is None):
        raise ValueError('derived_daily_parent_required')
    cutoff = date.fromisoformat(session)
    dates = [date.fromisoformat(r['date']) for r in rows]
    from app.services.vnext_dated_calendar import calendar_for_range
    _, cal = calendar_for_range(market, start=min(dates, default=cutoff), end=cutoff,
                                policy=calendar_policy)
    if not cal.is_session(session):
        raise ValueError('completed_session_not_trading_day')
    if dates != sorted(set(dates)):
        raise ValueError('timeframe_duplicate_or_ordering')
    tainted = set()
    if daily_parent is not None:
        q = inspect_normalized_ohlcv_rows(daily_parent, timeframe='daily')
        tainted = {bounds(date.fromisoformat(i.bar_date), timeframe)[0]
                   for i in q.issues if i.bar_date}
    completed, incomplete = [], []
    for row, day in zip(rows, dates):
        start, end = bounds(day, timeframe)
        sessions = cal.sessions_in_range(start.isoformat(), end.isoformat())
        if not len(sessions) or not cal.is_session(day.isoformat()):
            raise ValueError('timeframe_nontrading_bar')
        if date.fromisoformat(str(sessions[-1].date())) <= cutoff:
            completed.append(row)
        else:
            incomplete.append(day.isoformat())
    suffix, bad, newer = [], None, None
    for row in reversed(completed):
        day = date.fromisoformat(row['date'])
        q = inspect_normalized_ohlcv_rows([row], timeframe=timeframe, cutoff=cutoff)
        reasons = [str(i.violation) for i in q.issues]
        vol = row.get('volume')
        if type(vol) not in (int, float) or not math.isfinite(vol) or vol < 0:
            reasons.append('INVALID_VOLUME')
        if row.get('price_basis', basis) != basis:
            reasons.append('PRICE_BASIS_CHANGED')
        if bounds(day, timeframe)[0] in tainted:
            reasons.append('DERIVED_PERIOD_CONTAINS_INVALID_DAILY')
        if newer is not None:
            between = cal.sessions_in_range((day + timedelta(days=1)).isoformat(), newer.isoformat())
            if timeframe == 'daily':
                contiguous = len(between) == 1
            else:
                keys = {bounds(x.date(), timeframe)[0] for x in between}
                contiguous = keys <= {bounds(day, timeframe)[0], bounds(newer, timeframe)[0]}
                contiguous = contiguous and bounds(day, timeframe)[0] != bounds(newer, timeframe)[0]
            if not contiguous:
                reasons.append('PERIOD_GAP_OR_DUPLICATE')
        if reasons:
            bad = dict(date=row['date'], reasons=sorted(set(reasons)), row_sha256=canonical_fingerprint(row))
            if 'PERIOD_GAP_OR_DUPLICATE' in reasons:
                bad['calendar_expected_sessions_between'] = [str(x.date()) for x in between]
                bad['gap_meaning'] = 'SOURCE_CALENDAR_DISAGREEMENT_NOT_PROOF_OF_BAD_OHLC_OR_ACTUAL_TRADING'
            break
        suffix.append(deepcopy(row)); newer = day
    suffix.reverse()
    if suffix:
        start, end = bounds(cutoff, timeframe)
        sessions = cal.sessions_in_range(start.isoformat(), end.isoformat())
        expected_end = end if date.fromisoformat(str(sessions[-1].date())) <= cutoff else start - timedelta(days=1)
        while not cal.is_session(expected_end.isoformat()):
            expected_end -= timedelta(days=1)
        if bounds(date.fromisoformat(suffix[-1]['date']), timeframe) != bounds(expected_end, timeframe):
            bad = dict(date=suffix[-1]['date'], reasons=['LATEST_COMPLETED_PERIOD_MISSING'])
            suffix = []
    result = dict(contract=CONTRACT, timeframe=timeframe, source_kind=source_kind,
        session=session, basis=basis, full_source_rows=len(rows), completed_rows=len(completed),
        excluded_incomplete=incomplete, first_invalid=bad, rows=suffix,
        start=suffix[0]['date'] if suffix else None, end=suffix[-1]['date'] if suffix else None,
        count=len(suffix), status=(timeframe.upper()+'_TRUNCATED_USABLE' if bad else
            timeframe.upper()+'_USABLE') if suffix else 'UNAVAILABLE',
        raw_unchanged=True, strict_native=False, economic_use=False,
        recurrence_seed='EXISTING_ENGINE_RESEEDED_ON_EXPLICIT_CONTIGUOUS_VIEW',
        adjustment_action_authority='PROVIDER_RECORDED_BASIS_NOT_INDEPENDENT_CORPORATE_ACTION_PROOF')
    if calendar_policy is not None:
        result['calendar_policy'] = calendar_policy
    result['view_sha256'] = digest(result)
    return result


def _lagged_diagnostic(rows, *, timeframe, market, session, source_kind, basis,
                       daily_parent, policy, evidence):
    """One evidenced terminal anomaly only; this projection grants no use rights."""
    if (policy != DATED_DIAGNOSTIC_CONTRACT or timeframe != 'daily' or
            source_kind != 'NATIVE' or daily_parent is not None or
            basis != 'adjusted_close' or market not in APIS):
        raise ValueError('dated_diagnostic_policy_scope')
    if len(rows) < 2 or rows[-1]['date'] != session:
        raise ValueError('dated_exact_terminal_session_required')
    cutoff = date.fromisoformat(session)
    dates = [date.fromisoformat(r['date']) for r in rows]
    if dates != sorted(set(dates)) or dates[-1] > cutoff:
        raise ValueError('dated_duplicate_order_or_future_bar')
    _, cal = _calendar_for_range(market, start=dates[0], end=cutoff)
    expected = [str(x.date()) for x in cal.sessions_in_range(dates[0], cutoff)]
    if [r['date'] for r in rows] != expected:
        raise ValueError('dated_continuity_or_calendar_gap')
    for row in rows:
        volume = row.get('volume')
        if (type(volume) not in (int, float) or not math.isfinite(volume) or volume < 0
                or row.get('price_basis', basis) != basis
                or str(row.get('bar_state') or row.get('completion_state') or '').upper()
                in {'PROVISIONAL','PARTIAL','OPEN','LIVE','UNCONFIRMED','UNKNOWN'}):
            raise ValueError('dated_volume_basis_or_provisional')
    quality = inspect_normalized_ohlcv_rows(rows, timeframe='daily', cutoff=cutoff)
    anomalies = [dict(date=i.bar_date, reason=str(i.violation), row_sha256=i.row_fingerprint)
                 for i in quality.issues]
    latest = inspect_normalized_ohlcv_rows([rows[-1]], timeframe='daily', cutoff=cutoff)
    required = [dict(date=session, reason='LOW_GT_CLOSE', row_sha256=i.row_fingerprint)
                for i in latest.issues if str(i.violation)=='LOW_GT_CLOSE']
    if len(required) != 1:
        raise ValueError('dated_exact_terminal_anomaly_required')
    if anomalies != required or not isinstance(evidence, dict) or evidence.get('anomalies') != required:
        raise ValueError('dated_exact_terminal_anomaly_required')
    if any(not isinstance(evidence.get(k), str) or not evidence[k]
           for k in ('raw_source_generation','parent_raw_sha256','original_current_owner_status')):
        raise ValueError('dated_original_source_binding_required')
    as_of = rows[-2]['date']
    prior = analytic_view(rows[:-1], timeframe='daily', market=market, session=as_of, basis=basis)
    if prior['count'] != len(rows)-1 or prior['first_invalid'] is not None:
        raise ValueError('dated_nonterminal_defect')
    result = dict(contract=policy, requested_target_session=session,
        raw_source_generation=evidence['raw_source_generation'],
        parent_raw_sha256=evidence['parent_raw_sha256'],
        original_current_owner_status=evidence['original_current_owner_status'],
        excluded_bar_dates=[session], excluded_reason=anomalies,
        excluded_original_row_sha256=canonical_fingerprint(rows[-1]),
        analysis_as_of=as_of, valid_contiguous_count=prior['count'],
        stale_sessions=len(cal.sessions_in_range(as_of, session))-1,
        scope='DATED_DIAGNOSTIC_ONLY', intended_use='DATED_RESEARCH_ONLY',
        rows=prior['rows'], rows_sha256=digest(prior['rows']),
        basis=basis, timeframe='daily', source_kind='NATIVE',
        current_price_complete=False, current_price_owner='DENIED',
        quote_owner='QUOTE_SEMANTICS_UNCONFIRMED', strict_native=False,
        economic_direction_authority=False, research_admission=False,
        original_owner_grant=False, raw_unchanged=True,
        limitation='PURE_PROJECTION_NOT_CONSUMER_AUTHORITY; single terminal anomaly only')
    result['view_sha256'] = digest(result)
    return result


def replay_dated_diagnostic(owner, ticker, *, source_sha, session, as_of, parser_root, parser_pins):
    """Replay a denied original source without creating an alternative Owner.

    No dated-use issuance exists in the current DailyDelta/Composite contract.
    Features below are diagnostic candidates, never model-admissible facts.
    """
    from datetime import datetime
    from app.services.vnext_incremental_replay import SealedPublicReplay, capture_occurrence
    from app.services.vnext_price_capture import parse_original
    from app.services.vnext_public_capture import target_session
    from app.services.ohlcv_completed_bar_finality_service import annotate_normalized_bar
    if type(owner) is not SealedPublicReplay:
        raise ValueError('original_dated_replay_owner_required')
    original_proof = owner.verify_subject(ticker)
    batch = owner.batch()
    identity = batch['registrations'][ticker]['security']
    observations = [o for o in batch['observations'] if o['ticker']==ticker
        and o['field']=='ohlcv.adjusted_daily' and o['source_sha']==source_sha]
    if len(observations) != 1:
        raise ValueError('dated_original_observation_membership')
    observation = observations[0]
    cap = capture_occurrence(batch['captures'], observation['run_id'], source_sha)
    root = json.loads(cap['raw'])
    if (root.get('kind') != 'CURRENT_CHART_REPLAY' or observation['status']!='POLICY_DENIED'
            or root['quality']['valid'] is not False or observation['payload']['quality_valid'] is not False
            or observation['payload']['calendar'] != root['calendar']
            or observation['payload']['adjusted'] is not True):
        raise ValueError('dated_original_denial_required')
    _, calendar_identity = target_session(identity['country'].lower(), datetime.fromisoformat(root['calendar']['as_of']))
    if calendar_identity != root['calendar'] or calendar_identity['session'] != session:
        raise ValueError('dated_original_calendar_identity')
    receipts, parsed = [], []
    for page in root['pages']:
        parent = capture_occurrence(batch['captures'], observation['run_id'], page['raw_sha256'],
            captured_at=page['captured_at'], request_body=root['request_body'])
        captured = datetime.fromisoformat(page['captured_at'])
        if captured > datetime.fromisoformat(as_of) or str(target_session(identity['country'].lower(), captured)[0]) != session:
            raise ValueError('dated_original_capture_time')
        parsed_page = parse_original(json.loads(parent['raw']), identity['country'].lower(), 'daily', parser_root, parser_pins)
        if parsed_page['parser_sha256'] != root['parser_sha256']:
            raise ValueError('dated_parser_identity')
        parsed.extend(parsed_page['rows'])
        receipts.append(deepcopy(parent['receipt']))
    parsed_dates = [r['date'] for r in parsed]
    if len(parsed_dates)!=len(set(parsed_dates)) or parsed_dates not in (sorted(parsed_dates),sorted(parsed_dates,reverse=True)):
        raise ValueError('dated_original_page_order')
    if any(r['date']>session for r in parsed):
        raise ValueError('dated_provisional_source_not_backfilled')
    if sorted(parsed,key=lambda r:r['date'])[-root['requested_rows']:] != root['selected']:
        raise ValueError('dated_original_parser_projection')
    source_bytes = {c['raw_sha']: c['raw'].encode() for c in batch['captures']}
    entry = dict(source_sha=source_sha, original_run=observation['run_id'], status=observation['status'],
        provenance=dict(dependencies=[dict(raw_sha256=r['raw_sha256'],receipt_sha256=digest(r)) for r in receipts]))
    binding = dict(source_sha=source_sha,source_generation=observation['run_id'],receipts=receipts)
    current = replay_view(entry,source_bytes,identity=identity,timeframe='daily',session=session,binding=binding)
    if current['rows']:
        raise ValueError('dated_current_path_not_denied')
    quality = inspect_normalized_ohlcv_rows(root['selected'],timeframe='daily',cutoff=date.fromisoformat(session))
    evidence = dict(raw_source_generation=observation['run_id'],parent_raw_sha256=source_sha,
        original_current_owner_status=observation['status'],
        anomalies=[dict(date=i.bar_date,reason=str(i.violation),row_sha256=i.row_fingerprint) for i in quality.issues])
    dated = analytic_view(root['selected'],timeframe='daily',market=identity['country'],session=session,
        lagged_end_policy=DATED_DIAGNOSTIC_CONTRACT,terminal_evidence=evidence)
    annotated = [annotate_normalized_bar(r,provider='kiwoom',market=identity['country'],
        timeframe='daily',has_later_chart_row=True) for r in dated['rows']]
    features = build_multi_timeframe_feature_packet(ticker=ticker,periods={'daily':annotated},
        cutoff=date.fromisoformat(dated['analysis_as_of'])).model_dump(mode='json')['daily']
    result = dict(contract=DATED_DIAGNOSTIC_CONTRACT,security=deepcopy(identity),
        original_owner_proof=original_proof,current_view=current,dated_analytic_view=dated,
        diagnostic_features=features, permitted_indicators=[],
        diagnostic_indicator_candidates=[f['semantic'] for f in features['facts']],
        can_issue_dated_research=False, exact_first_blocker='DATED_VIEW_ORIGINAL_CONSUMER_AUTHORITY_MISSING',
        source_use='DATED_DIAGNOSTIC_ONLY', model_admissible=False,
        strict_native=False, economic_direction_authority=False, send=False)
    result['replay_sha256'] = digest(result)
    return result


def bind_owned_inputs(owner, ticker):
    """Exact HTTP receipt bindings obtained only from the live original owner."""
    from app.services.vnext_incremental_replay import SealedPublicReplay
    if not isinstance(owner, SealedPublicReplay):
        raise ValueError('original_timeframe_owner_required')
    owner.verify_subject(ticker)
    batch = owner.batch()
    caps = {(c['run_id'], c['raw_sha']): c for c in batch['captures']}
    result = {}
    for ob in batch['observations']:
        if ob['ticker'] != ticker or ob['field'] not in ['ohlcv.adjusted_'+tf for tf in APIS['US']]:
            continue
        cap = caps[ob['run_id'], ob['source_sha']]
        root = json.loads(cap['raw'])
        if root.get('kind') != 'CURRENT_CHART_REPLAY':
            continue  # Incremental contracts retain their existing separate replay.
        tf = ob['field'].split('_')[-1]
        receipts = [deepcopy(caps[ob['run_id'], p['raw_sha256']]['receipt']) for p in root['pages']]
        result[tf] = dict(source_sha=ob['source_sha'], source_generation=ob['run_id'],
            receipts=receipts, allowed_use='DATED_ANALYTIC_RESEARCH_ONLY')
    return result


def replay_view(entry, source_bytes, *, identity, timeframe, session, binding):
    """Consumer reproof of exact parent bytes, request period and receipt hashes."""
    raw = source_bytes[entry['source_sha']]
    if digest(raw) != entry['source_sha'] or binding['source_sha'] != entry['source_sha']:
        raise ValueError('timeframe_original_hash')
    root = json.loads(raw)
    if root.get('kind') != 'CURRENT_CHART_REPLAY' or root['calendar']['session'] != session:
        raise ValueError('timeframe_original_contract')
    if binding['source_generation'] != entry['original_run']:
        raise ValueError('timeframe_original_generation')
    body = root['request_body']; market = identity['country']
    if (body.get('stk_cd') != identity['ticker'].replace('.', '-') or body.get('upd_stkpc_tp') != '1'
        or root['calendar']['calendar'] != ('XKRX' if market == 'KR' else 'XNYS')
        or (market == 'US' and body.get('stex_tp') != {'NASDAQ':'ND','NYSE':'NY','AMEX':'NA'}.get(identity['exchange']))):
        raise ValueError('timeframe_identity_or_basis')
    pages = root['pages']; receipts = binding['receipts']
    if not pages or len(pages) != len(receipts):
        raise ValueError('timeframe_page_bindings')
    dependencies = entry['provenance']['dependencies']
    for page, receipt in zip(pages, receipts):
        sha = page['raw_sha256']
        if (digest(source_bytes[sha]) != sha or receipt.get('raw_sha256') != sha
            or receipt.get('raw_birth') != 'CURRENT_HTTP' or receipt.get('status') != 200
            or receipt.get('auth') is True or receipt.get('run_id') != binding['source_generation']
            or receipt.get('captured_at') != page['captured_at']
            or receipt['request'].get('api') != APIS[market][timeframe]
            or json.loads(receipt['request']['body']) != body
            or not any(d['raw_sha256'] == sha and d['receipt_sha256'] == digest(receipt) for d in dependencies)):
            raise ValueError('timeframe_HTTP_receipt_mismatch')
    view = analytic_view(root['selected'], timeframe=timeframe, market=market, session=session)
    view.update(parent_raw_sha256=entry['source_sha'], page_sha256=[p['raw_sha256'] for p in pages],
        original_full_status=entry['status'], original_full_quality=root['quality']['valid'],
        parser_sha256=root['parser_sha256'], source_generation=binding['source_generation'])
    features = build_multi_timeframe_feature_packet(ticker=identity['ticker'],
        periods={timeframe:view['rows']}, cutoff=date.fromisoformat(session)).model_dump(mode='json')[timeframe]
    view['features'] = features
    view['permitted_indicators'] = [f['semantic'] for f in features['facts']]
    view['consumer_input_sha256'] = digest(view)
    return view
