"""Offline, source-bound incremental replay. No network or investment authority.

The trusted bootstrap supplies the original reviewed refresh capability. Splitting
a sealed chart demonstrates a merge, not two historical capture events. Derived
rows never become replacement provider receipts or current-use grants.
"""
from copy import deepcopy
from datetime import date, datetime
import json

from app.services.vnext_research_store import digest
from app.services.vnext_public_refresh_ingestion import ReviewedPublicRefresh
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
from app.services.kiwoom_completed_close_owner import validate_completed_daily_row
from app.services.market_session import _exchange_calendar

CONTRACT = 'sealed-public-incremental-replay-v1'


def capture_occurrence(captures, run, sha, *, captured_at=None, request_body=None):
    """CAS identifies bytes; time and request identify the original HTTP event."""
    matches = [c for c in captures if c['run_id'] == run and c['raw_sha'] == sha]
    if captured_at is not None:
        matches = [c for c in matches if c['receipt']['captured_at'] == captured_at]
    if request_body is not None:
        matches = [c for c in matches if
                   json.loads(c['receipt'].get('request', {}).get('body') or '{}') == request_body]
    if len(matches) != 1:
        raise ValueError('original_capture_occurrence_missing_or_ambiguous')
    return matches[0]


def verify_completed_projection(identity, raw, receipt, payload):
    """Re-enter the original close validator on ingestion and cold consumption."""
    from app.services.vnext_public_capture import target_session
    p = payload
    target, calendar = target_session(identity['country'].lower(), datetime.fromisoformat(p['calendar']['as_of']))
    if calendar != p['calendar'] or p['currency'] != ('KRW' if identity['country'] == 'KR' else 'USD'):
        raise ValueError('completed_close_currency_or_calendar')
    if identity['country'] == 'US':
        request = receipt['request']; body = json.loads(request['body'])
        if request['api'] != 'usa20590' or body['stk_cd'] != identity['ticker'] or body['base_dt'] != target.strftime('%Y%m%d'):
            raise ValueError('completed_close_original_request_identity')
        row, integrity = validate_completed_daily_row(raw, target)
        if row != p['row'] or integrity.model_dump(mode='json') != p['integrity']:
            raise ValueError('original_completed_close_replay')
    else:
        original = json.loads(raw)
        if original['selected'][-1] != p['row']:
            raise ValueError('original_KR_close_row_mismatch')
        quality = inspect_normalized_ohlcv_rows([p['row']], timeframe='daily', cutoff=target)
        if not quality.valid or p['row']['date'] != p['calendar']['session']:
            raise ValueError('original_KR_close_quality')


def merge_daily(previous, tail, *, market, session, previous_basis, tail_basis,
                correction_reason=None, requested_rows=1000):
    if market not in ('KR', 'US') or not previous or not tail or requested_rows < 1:
        raise ValueError('bounded_daily_merge_required')
    if previous_basis != tail_basis:
        raise ValueError('price_basis_changed_requires_original_owner_requalification')
    required = {'security', 'currency', 'adjusted', 'calendar', 'role'}
    if not required <= previous_basis.keys() or previous_basis['role'] != 'daily':
        raise ValueError('explicit_price_basis_required')
    expected_calendar = 'XKRX' if market == 'KR' else 'XNYS'
    if previous_basis['calendar'] != expected_calendar:
        raise ValueError('wrong_market_calendar')
    for rows in (previous, tail):
        dates = [r['date'] for r in rows]
        if dates != sorted(set(dates)) or any(d > session for d in dates):
            raise ValueError('duplicate_or_uncompleted_bar')
    merged = {r['date']: deepcopy(r) for r in previous}
    changes, corrections = [], []
    for row in tail:
        old = merged.get(row['date'])
        if old is not None and old != row:
            if not correction_reason:
                raise ValueError('same_session_revision_requires_reason')
            corrections.append(dict(session=row['date'], old=digest(old), new=digest(row), reason=correction_reason))
        if old != row:
            changes.append(row['date'])
        merged[row['date']] = deepcopy(row)
    rows = [merged[d] for d in sorted(merged)]
    cal = _exchange_calendar(expected_calendar)
    if any(not cal.is_session(d) for d in merged):
        raise ValueError('non_trading_session_bar')
    sessions = [str(x.date()) for x in cal.sessions_in_range(previous[-1]['date'], session)]
    gaps = [d for d in sessions if d not in merged]
    quality = inspect_normalized_ohlcv_rows(rows, timeframe='daily', cutoff=date.fromisoformat(session)).model_dump(mode='json')
    status = ('NEEDS_BOUNDED_BACKFILL' if gaps else 'LATEST_COMPLETED_SESSION_MISSING' if rows[-1]['date'] != session
              else 'ORIGINAL_QUALITY_DENIED' if not quality['valid'] else 'SHORT_HISTORY' if len(rows) < requested_rows
              else 'MERGED_RESEARCH_WINDOW')
    return dict(contract=CONTRACT, status=status, rows=rows[-requested_rows:], merged_rows=len(rows),
                previous_session=previous[-1]['date'], session=session, missing_sessions=gaps,
                changed_sessions=changes, corrections=corrections, quality=quality,
                prior_sha256=digest(previous), tail_sha256=digest(tail), merged_sha256=digest(rows),
                basis=deepcopy(previous_basis), original_owner_grant=False, weekly_changed=False,
                monthly_changed=False, physical_HTTP=0, strict_native=False)


class SealedPublicReplay:
    """Backend-only capability pinned to an original reviewed ingestion owner."""
    def __init__(self, owner):
        if not isinstance(owner, ReviewedPublicRefresh):
            raise ValueError('live_original_refresh_owner_required')
        self.owner = owner
        self.pin = digest(owner.batch())

    def batch(self):
        batch = self.owner.batch()
        if digest(batch) != self.pin:
            raise ValueError('sealed_refresh_drift')
        for c in batch['captures']:
            r=c['receipt']
            if r.get('raw_birth')=='CURRENT_HTTP' and (r.get('run_id')!=c['run_id'] or
                    r.get('raw_sha256')!=c['raw_sha'] or r.get('status')!=200 or r.get('auth') is True):
                raise ValueError('original_HTTP_receipt_scope')
        return batch

    def verify_subject(self, ticker):
        b = self.batch()
        if ticker not in b['registrations']:
            raise ValueError('source_registration_membership')
        identity = b['registrations'][ticker]['security']
        def cap_at(run, sha, **binding):
            return capture_occurrence(b['captures'], run, sha, **binding)
        def chart(cap):
            original = json.loads(cap['raw'])
            if original.get('contract') != 'owned-incremental-daily-research-v1':
                return original
            from app.services.vnext_rolling_chart import resolve_chart, MAX_NODES, MAX_DEPTH
            closure, active = {}, set()
            def collect(run, sha, depth, occurrence=None):
                key = (run, sha)
                if depth > MAX_DEPTH + 2 or key in active or len(closure) >= MAX_NODES:
                    raise ValueError('incremental_source_closure_bound_or_cycle')
                if key in closure:
                    return
                c = occurrence or cap_at(run, sha); data = c['raw'].encode()
                if digest(data) != sha:
                    raise ValueError('incremental_source_raw_drift')
                active.add(key)
                node = json.loads(data)
                if node.get('contract') == 'owned-incremental-daily-research-v1':
                    for p in node['parents']:
                        collect(p['run_id'], p['raw_sha256'], depth + 1)
                elif node.get('kind') == 'CURRENT_CHART_REPLAY':
                    for p in node['pages']:
                        page = cap_at(run, p['raw_sha256'], captured_at=p['captured_at'],
                                      request_body=node['request_body'])
                        if (page['receipt']['captured_at'] != p['captured_at'] or
                                json.loads(page['receipt']['request']['body']) != node['request_body']):
                            raise ValueError('chart_original_page_receipt')
                        collect(run, p['raw_sha256'], depth + 1, page)
                closure[key] = dict(run_id=run, raw_sha256=sha, receipt_sha256=digest(c['receipt']))
                active.remove(key)
            for p in original['parents']:
                collect(p['run_id'], p['raw_sha256'], 0)
            entry = dict(field='ohlcv.adjusted_daily', source_sha=cap['raw_sha'],
                provenance=dict(provider=cap['provider'], dependencies=original['parents'],
                                dependency_closure=list(closure.values())))
            return resolve_chart(entry, {c['raw_sha']:c['raw'].encode() for c in b['captures']}, security=identity)
        proofs = []
        for o in b['observations']:
            if o['ticker'] != ticker:
                continue
            cap = cap_at(o['run_id'], o['source_sha'])
            original = json.loads(cap['raw'])
            if o['field'].startswith('ohlcv.'):
                original = chart(cap)
                if original.get('request_body', {}).get('stk_cd') != ticker.replace('.', '-'):
                    raise ValueError('chart_security_membership')
                for page in original['pages']:
                    binding = dict(captured_at=page['captured_at'])
                    if original.get('contract') != 'owned-incremental-daily-research-v1':
                        binding['request_body'] = original['request_body']
                    parent = cap_at(page.get('original_run',o['run_id']), page['raw_sha256'], **binding)
                    if digest(parent['raw'].encode()) != page['raw_sha256'] or parent['receipt']['captured_at'] != page['captured_at']:
                        raise ValueError('chart_original_page_receipt')
                    if (original.get('contract') != 'owned-incremental-daily-research-v1' and
                            json.loads(parent['receipt']['request']['body'])!=original['request_body']):
                        raise ValueError('chart_original_request_identity')
                if original['calendar']['calendar']!=('XKRX' if identity['country']=='KR' else 'XNYS'):
                    raise ValueError('chart_original_market_calendar')
                if o['field'] == 'ohlcv.adjusted_daily':
                    rows = original['selected']
                    if len(rows) < 2:
                        proofs.append(dict(field=o['field'], status='SHORT_HISTORY', source_sha=o['source_sha']))
                        continue
                    basis = dict(security=identity['canonical_security_id'], currency='KRW' if identity['country']=='KR' else 'USD',
                                 adjusted=o['payload']['adjusted'], calendar='XKRX' if identity['country']=='KR' else 'XNYS', role='daily')
                    merge = merge_daily(rows[:-1], rows[-1:], market=identity['country'], session=original['calendar']['session'],
                                        previous_basis=basis, tail_basis=basis, requested_rows=original['requested_rows'])
                    if merge['rows'] != rows:
                        raise ValueError('merged_rows_not_original_sealed_selection')
                    proofs.append(dict(field=o['field'], source_sha=o['source_sha'], source_generation=o['run_id'],
                        receipt_sha256=digest(cap['receipt']), captured_at=cap['receipt']['captured_at'], merge=merge,
                        original_status=o['status'], original_quality=o['payload']['quality_valid'],
                        provenance='SEALED_SERIES_SPLIT_REPLAY_NOT_TWO_CAPTURES', new_live_raw=False))
            elif o['field'] == 'completed_close':
                p = o['payload']
                verify_completed_projection(identity, cap['raw'].encode(), cap['receipt'], p)
                proofs.append(dict(field=o['field'], source_sha=o['source_sha'], source_generation=o['run_id'],
                    status='ORIGINAL_COMPLETED_CLOSE_REPLAY_PASS', calendar=p['calendar'],
                    adjustment=p.get('adjustment',p.get('adjusted')), receipt_sha256=digest(cap['receipt'])))
        return dict(contract=CONTRACT, security=identity, registration_version=b['registrations'][ticker]['registration_version'],
                    proofs=proofs, raw_generation_unchanged=True, current_source_requalification=False)


def release_inventory(owner, *, previous=(), checked_providers=()):
    """Discover exact releases in owned bytes; missing discovery is NOT_CHECKED.

    Metadata here only proposes acquisition/replay. It never qualifies a financial
    cell or asserts that an uninspected later filing is economically irrelevant.
    """
    if not isinstance(owner, SealedPublicReplay):
        raise ValueError('owned_release_inventory_required')
    batch = owner.batch()
    events, unparsed = [], []
    for c in batch['captures']:
        r = c['receipt']
        if r.get('raw_birth') != 'CURRENT_HTTP' or r.get('status') != 200:
            continue
        try:
            raw = json.loads(c['raw'])
        except json.JSONDecodeError:
            unparsed.append(dict(raw_sha256=c['raw_sha'],provider=c['provider'],
                status='NON_JSON_METADATA_NOT_CLASSIFIED',financial_meaning='NOT_INFERRED'))
            continue
        provider = c['provider']
        rows = []
        recent = raw.get('filings', {}).get('recent', {}) if isinstance(raw, dict) else {}
        if recent and isinstance(recent.get('accessionNumber'), list):
            n = len(recent['accessionNumber'])
            if any(len(recent.get(k, [])) != n for k in ('form','filingDate')):
                raise ValueError('release_metadata_parallel_arrays')
            rows = [dict(issuer=str(raw.get('cik')), accession=recent['accessionNumber'][i],
                form=recent['form'][i], published=recent['filingDate'][i],
                reported_period=recent.get('reportDate',['']*n)[i], amendment=recent['form'][i].endswith('/A')) for i in range(n)]
        elif isinstance(raw,dict) and isinstance(raw.get('list'),list):
            rows = [dict(issuer=x.get('corp_code'),accession=x['rcept_no'],form=x.get('report_nm'),
                         published=x.get('rcept_dt'),reported_period=None,amendment=None)
                    for x in raw['list'] if isinstance(x,dict) and x.get('rcept_no')]
        elif provider.lower() in ('kis','finnhub','fred','ecos'):
            # A snapshot is not evidence that no newer release exists.
            rows = [dict(issuer=None,accession=digest(raw),form='OBSERVED_SNAPSHOT',
                         published=None,reported_period=None,amendment=None)]
        for row in rows:
            event = dict(row,provider=provider,raw_sha256=c['raw_sha'],source_generation=c['run_id'],
                         captured_at=r['captured_at'],receipt_sha256=digest(r),request_key=c['request_key'])
            event['event_id'] = digest([provider,row])
            event['reported_period_is_metadata_not_statement_authority'] = True
            events.append(event)
    old = {x['event_id'] for x in previous}
    return dict(events=events, new=[x for x in events if x['event_id'] not in old],unparsed=unparsed,
                current_discovery={p:('SEALED_METADATA_REPLAY_ONLY' if p in checked_providers else 'NOT_CHECKED')
                    for p in ('SEC','OpenDART','KIS','Finnhub','FRED','ECOS')},
                no_new_release_asserted=False,physical_HTTP=0,financial_use_granted=False)
