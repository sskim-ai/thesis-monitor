"""Receipt-bound, limited current parents. No FullMarket or financial use grant."""
from datetime import datetime, timedelta, timezone
import json

from app.services.vnext_incremental_replay import SealedPublicReplay, release_inventory
from app.services.vnext_research_store import digest

CONTRACT = 'bounded-current-parent-replay-v1'


def _captures(owner, provider, observed_at):
    if type(owner) is not SealedPublicReplay:
        raise ValueError('original_sealed_replay_required')
    at = datetime.fromisoformat(observed_at)
    if at.tzinfo is None:
        raise ValueError('parent_explicit_observation_time_required')
    captures = owner.batch()['captures']
    if not captures or len(captures) > 8:
        raise ValueError('bounded_parent_capture_set_required')
    for c in captures:
        r = c['receipt']
        captured = datetime.fromisoformat(r['captured_at'])
        if (c['provider'] != provider or r.get('raw_birth') != 'CURRENT_HTTP' or
                r.get('provider') != provider or r.get('request_key') != c['request_key'] or
                digest(r.get('request')) != c['request_key'] or
                r.get('status') != 200 or r.get('auth') is not False or
                captured.tzinfo is None or not timedelta(0) <= at-captured <= timedelta(minutes=15) or
                r.get('run_id') != c['run_id'] or r.get('raw_sha256') != c['raw_sha'] or
                digest(c['raw'].encode()) != c['raw_sha']):
            raise ValueError('parent_original_capture_identity_or_time')
    return captures


def opendart_discovery(owner, *, scope, query, observed_at):
    """Empty is meaningful only for an exact successful completed query.

    A complete two-page discovery window is not a complete issuer history, a
    document inspection, or permission to use a financial statement.
    """
    if (scope.get('provider') != 'OpenDART' or set(query) != {'begin','end','page_count','max_pages'} or
            not 1 <= query['max_pages'] <= 8 or not 1 <= query['page_count'] <= 100):
        raise ValueError('release_bounded_query_required')
    begin, end = (datetime.strptime(query[k], '%Y%m%d').date() for k in ('begin','end'))
    at = datetime.fromisoformat(observed_at)
    if begin > end or end > at.date() or (end-begin).days > 31:
        raise ValueError('release_query_period')
    captures = _captures(owner, 'OpenDART', observed_at)
    if len(captures) > query['max_pages']:
        raise ValueError('release_page_budget')
    pages, totals = {}, set()
    for c in captures:
        r = c['receipt']; req = r['request']; q = dict(req['query'])
        if (req.get('host') != 'opendart.fss.or.kr' or req.get('path') != '/api/list.json' or
                req.get('method') != 'GET' or set(q) != {'corp_code','bgn_de','end_de','page_count','page_no'} or
                q['corp_code'] != str(scope['issuer']) or q['bgn_de'] != query['begin'] or
                q['end_de'] != query['end'] or int(q['page_count']) != query['page_count']):
            raise ValueError('release_original_query_binding')
        ordinal = int(q['page_no']); raw = json.loads(c['raw'])
        if ordinal in pages or not 1 <= ordinal <= query['max_pages']:
            raise ValueError('release_page_identity')
        rows = raw.get('list', [])
        if raw.get('status') == '013':
            if ordinal != 1 or rows or len(captures) != 1 or int(raw.get('total_count', 0)):
                raise ValueError('release_empty_response_conflict')
            totals.add((0,0))
        elif raw.get('status') == '000':
            total, count = int(raw['total_page']), int(raw['total_count'])
            if (int(raw['page_no']) != ordinal or int(raw['page_count']) != query['page_count'] or
                    not isinstance(rows, list) or count <= 0 or total != (count+query['page_count']-1)//query['page_count'] or
                    ordinal > total or len(rows) != min(query['page_count'], count-(ordinal-1)*query['page_count'])):
                raise ValueError('release_page_accounting')
            totals.add((total,count))
        else:
            raise ValueError('release_provider_status_not_success_or_empty')
        for row in rows:
            if (row.get('corp_code') != str(scope['issuer']) or not row.get('rcept_no') or
                    not row.get('report_nm') or not query['begin'] <= row.get('rcept_dt','') <= query['end']):
                raise ValueError('release_event_issuer_or_period')
        pages[ordinal] = c
    if len(totals) != 1 or set(pages) != set(range(1,len(pages)+1)):
        raise ValueError('release_inconsistent_or_missing_pages')
    total, count = totals.pop()
    events = release_inventory(owner)['events']
    if len({e['accession'] for e in events}) != len(events):
        raise ValueError('release_duplicate_event_across_pages')
    complete = total <= len(pages) and len(events) == count
    return dict(contract=CONTRACT, kind='OPENDART_METADATA_QUERY', scope=scope, query=query,
        state=('EMPTY' if count == 0 else 'OWNER_ACCEPTED') if complete else 'PENDING',
        coverage='BOUNDED_QUERY_COMPLETE_AS_OF_CAPTURE' if complete else 'PAGES_REMAIN',
        query_watermark=query['end'] if complete else None, observed_at=observed_at,
        complete=complete, pages_observed=len(pages), total_pages=total, total_events=count, events=events,
        source_pin=owner.pin, receipts=[dict(raw_sha256=c['raw_sha'],receipt_sha256=digest(c['receipt']),
            source_generation=c['run_id'],captured_at=c['receipt']['captured_at']) for c in captures],
        financial_use_granted=False, document_contents_checked=False, physical_HTTP=0)


def kr_completed_indices(owner, *, observed_at):
    from app.services.vnext_public_capture import target_session
    from app.services.kiwoom_kr_market_context_service import KiwoomKrMarketContextService, kiwoom_market_reads, SECTOR_ENDPOINT
    at = datetime.fromisoformat(observed_at)
    target, calendar = target_session('kr', at)
    reads = [r for r in kiwoom_market_reads(session_date=target,max_pages=1,max_requests_per_page=1) if r.api_id == 'ka20009']
    captures = _captures(owner, 'Kiwoom', observed_at)
    if len(captures) != len(reads):
        raise ValueError('market_exact_component_set_required')
    components, used = [], set()
    for read in reads:
        matches = [c for c in captures if c['receipt']['request'].get('api') == read.api_id and
                   json.loads(c['receipt']['request'].get('body') or '{}') == read.body]
        if len(matches) != 1:
            raise ValueError('market_original_component_request')
        c = matches[0]; req = c['receipt']['request']
        if (req.get('host') != 'api.kiwoom.com' or req.get('path') != SECTOR_ENDPOINT or req.get('method') != 'POST' or
                c['capture_id'] in used):
            raise ValueError('market_original_endpoint')
        used.add(c['capture_id'])
        row = KiwoomKrMarketContextService._completed_history_row(history=json.loads(c['raw']),session_date=target,observed_at=at)
        components.append(dict(component=read.key,row=row,raw_sha256=c['raw_sha'],receipt_sha256=digest(c['receipt']),
            source_generation=c['run_id'],captured_at=c['receipt']['captured_at']))
    return dict(contract=CONTRACT,kind='KR_COMPLETED_INDEX_COMPONENTS',state='OWNER_ACCEPTED',
        observed_at=observed_at,calendar=calendar,watermark=str(target),components=components,
        source_pin=owner.pin, full_market_owner=False, direction_granted=False,
        unqueried={k:'NOT_CHECKED' for k in ('breadth','flow','sector','FX','macro','night_market')},physical_HTTP=0)


class CurrentParentReview:
    """Live revalidation callback for FreshDailyAuthority, not a JSON grant."""
    def __init__(self, *, market=None, release=None, required_for=None):
        self._market, self._release = market, release
        self._required = required_for or {'market':[], 'release':[]}
        if set(self._required) != {'market','release'} or any(not isinstance(v,list) for v in self._required.values()):
            raise ValueError('parent_required_axes')
        if any(f is not None and not callable(f) for f in (market,release)):
            raise ValueError('parent_live_replay_callbacks_required')
        self._pin = digest(self._required)

    def __call__(self, packet, registry):
        if digest(self._required) != self._pin:
            raise ValueError('parent_required_axes_drift')
        result = {}
        for name, replay in (('market',self._market),('release',self._release)):
            proof = replay() if replay is not None else None
            if proof is not None and proof.get('contract') != CONTRACT:
                raise ValueError('current_parent_original_replay_required')
            if proof is not None:
                observed=datetime.fromisoformat(proof['observed_at'])
                if observed.tzinfo is None or not timedelta(0) <= datetime.now(timezone.utc)-observed <= timedelta(minutes=15):
                    raise ValueError('current_parent_expired_or_future')
            result[name] = dict(state=proof['state'] if proof else 'NOT_CHECKED',
                watermark=proof.get('watermark',proof.get('query_watermark')) if proof else None,
                required_for=list(self._required[name]),original_contract=CONTRACT,
                receipt_sha256=digest(proof) if proof else None)
        return result
