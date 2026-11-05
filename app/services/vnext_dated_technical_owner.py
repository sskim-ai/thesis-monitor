"""Opt-in dated technical references, not current-price or economic authority."""
from copy import deepcopy
from datetime import date, datetime, timedelta
import json
import time

from app.services.ohlcv_completed_bar_finality_service import annotate_normalized_bar
from app.services.ohlcv_feature_engine_service import build_multi_timeframe_feature_packet
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
from app.services.unified_stock_acquisition import StockPlan, decode_owned_role
from app.services.vnext_incremental_replay import SealedPublicReplay, capture_occurrence
from app.services.vnext_price_capture import parse_original
from app.services.vnext_research_store import digest
from app.services.vnext_timeframe_views import APIS, analytic_view, bounds
from app.services.vnext_composite_research import PUBLIC_ID
from app.services.vnext_dated_calendar import POLICY as CALENDAR_POLICY, calendar_for_range

CONTRACT = 'dated-native-technical-reference-v1'
CONSUMER = 'vnext_optional_research_context'
USE = 'DATED_VALID_TECHNICAL_HISTORY'
TARGETS = {'daily': 1000, 'weekly': 700, 'monthly': 300}
PROHIBITED = ['CURRENT_PRICE', 'RTH_SETTLED_CLOSE', 'TIMING', 'VALUATION',
              'OVERALL_DIRECTION', 'STRICT_NATIVE', 'SEND']


def _parsed(pages, market, timeframe, parser_root, parser_pins):
    # Invoke the pinned original parser once for the verified page sequence.
    keys = [set(k for k, v in p.items() if isinstance(v, list)) for p in pages]
    common = set.intersection(*keys)
    if len(common) != 1:
        raise ValueError('history_ambiguous_rows')
    key = common.pop()
    body = deepcopy(pages[0])
    body[key] = [r for p in pages for r in p[key]]
    parsed = parse_original(body, market.lower(), timeframe, parser_root, parser_pins)
    dates = [r['date'] for r in parsed['rows']]
    if len(set(dates)) != len(dates) or dates not in (sorted(dates), sorted(dates, reverse=True)):
        raise ValueError('history_page_duplicate_or_order')
    return sorted(parsed['rows'], key=lambda r: r['date']), parsed['parser_sha256']


class CapturedScopedStockPlan:
    """Exact old Worker bytes for dated replay, NOT a current StockPlan grant."""
    __slots__=('_raw',)

    def __init__(self, value):
        from app.services.scoped_source_plan import ScopedStockRead
        required={'contract','run_id','acquisition_id','frozen_at','reads','owner_files'}
        if (set(value)!=required or value['contract']!='current-scoped-stock-capture-v1'
                or not value['owner_files'] or not value['reads']):
            raise ValueError('history_exact_scoped_worker_plan_required')
        if datetime.fromisoformat(value['frozen_at']).utcoffset() is None:
            raise ValueError('history_original_scoped_plan_time')
        reads=tuple(ScopedStockRead.model_validate(r) for r in value['reads'])
        if len({r.entry_id for r in reads})!=len(reads):
            raise ValueError('history_original_scoped_duplicate_role')
        object.__setattr__(self,'_raw',json.dumps(value,sort_keys=True,allow_nan=False))

    def __setattr__(self,name,value):
        raise AttributeError('history_original_scoped_plan_immutable')

    @property
    def run_id(self):return self.model_dump()['run_id']

    @property
    def acquisition_id(self):return self.model_dump()['acquisition_id']

    @property
    def frozen_at(self):return datetime.fromisoformat(self.model_dump()['frozen_at'])

    @property
    def reads(self):
        from app.services.scoped_source_plan import ScopedStockRead
        return tuple(ScopedStockRead.model_validate(r) for r in self.model_dump()['reads'])

    def model_dump(self, **kwargs):
        return json.loads(self._raw)


class LegacyChartReplay:
    """Backend byte capability; reuse the original stock receipt validator."""
    def __init__(self, *, plan, receipts, artifact_reader, parser_root, parser_pins):
        if type(plan) not in (StockPlan,CapturedScopedStockPlan) or not callable(artifact_reader):
            raise ValueError('history_original_plan_reader_required')
        self.plan, self.receipts, self.read = plan, deepcopy(receipts), artifact_reader
        self.root, self.pins = parser_root, parser_pins
        self._pin = digest([plan.model_dump(mode='json'), receipts])
        self._revoked = False

    def revoke(self):
        self._revoked = True

    def replay(self, security, timeframe):
        if self._revoked or digest([self.plan.model_dump(mode='json'), self.receipts]) != self._pin:
            raise ValueError('history_original_owner_changed_or_revoked')
        selected = [r for r in self.plan.reads if r.subject == security['ticker']
                    and r.timeframe == timeframe and r.adjusted]
        if len(selected) != 1:
            raise ValueError('history_original_role_membership')
        r = selected[0]
        exchange = {'NASDAQ': 'ND', 'NYSE': 'NY', 'AMEX': 'NA'}.get(security['exchange'], security['exchange'])
        if (r.canonical_security_id != security['canonical_security_id'] or
                r.market.upper() != security['country'] or r.exchange != exchange):
            raise ValueError('history_security_binding')
        receipt = self.receipts[r.entry_id]
        rows = decode_owned_role(self.plan, r, receipt, self.read)
        bodies, previous, seen = [], {'cont_yn': 'N', 'next_key': ''}, set()
        for p in receipt['pages']:
            if p['request']['continuation'] != previous or previous['next_key'] in seen:
                raise ValueError('history_continuation_chain')
            seen.add(previous['next_key'])
            previous = p['response_continuation']
            raw = self.read(p['artifact'], p['source_sha256'])
            if digest(raw) != p['source_sha256']:
                raise ValueError('history_raw_hash')
            bodies.append(json.loads(raw))
        parsed, parser_sha = _parsed(bodies, r.market, timeframe, self.root, self.pins)
        if parsed[-r.count:] != rows:
            raise ValueError('history_original_parser_projection')
        return dict(security=deepcopy(security), timeframe=timeframe, rows=rows,
            last_raw_date=parsed[-1]['date'], source_generation=self.plan.run_id,
            source_sha256=receipt['normalized_sha256'], receipt_sha256=digest(receipt),
            page_sha256=[p['source_sha256'] for p in receipt['pages']],
            requested_source_session=r.latest_completed_session,
            captured_at=receipt['completed_at'], parser_sha256=parser_sha,
            basis='adjusted_close', source_kind='NATIVE_SCOPED_HISTORICAL_V1' if type(self.plan) is CapturedScopedStockPlan else 'NATIVE',
            source_exhausted=previous['cont_yn'] != 'Y')


def _public_replay(owner, security, timeframe, parser_root, parser_pins):
    if type(owner) is not SealedPublicReplay:
        raise ValueError('history_original_public_owner_required')
    code = security['ticker']
    owner.verify_subject(code)
    b = owner.batch()
    registered = b['registrations'][code]['security']
    if (not all(security.get(k) for k in ('ticker', 'canonical_security_id', 'canonical_company_id', 'country', 'exchange'))
            or any(registered.get(k) != security.get(k) for k in (*PUBLIC_ID, 'company_name'))):
        raise ValueError('history_security_binding')
    observations = [o for o in b['observations'] if o['ticker'] == code
                    and o['field'] == 'ohlcv.adjusted_' + timeframe]
    if len(observations) != 1:
        raise ValueError('history_exact_role_required')
    ob = observations[0]
    cap = capture_occurrence(b['captures'], ob['run_id'], ob['source_sha'])
    root = json.loads(cap['raw'])
    body = root['request_body']
    expected_exchange = {'NASDAQ': 'ND', 'NYSE': 'NY', 'AMEX': 'NA'}.get(security['exchange'])
    if (root.get('kind') != 'CURRENT_CHART_REPLAY' or body.get('upd_stkpc_tp') != '1'
            or body.get('stk_cd') != code.replace('.', '-')
            or security['country'] == 'US' and body.get('stex_tp') != expected_exchange
            or root['calendar']['calendar'] != ('XKRX' if security['country'] == 'KR' else 'XNYS')):
        raise ValueError('history_source_identity_basis')
    bodies, receipts, seen, cursor = [], [], set(), ''
    for index, page in enumerate(root['pages'], 1):
        parent = capture_occurrence(b['captures'], ob['run_id'], page['raw_sha256'],
            captured_at=page['captured_at'], request_body=body)
        receipt = parent['receipt']
        request = receipt['request']
        if (page['ordinal'] != index or cursor in seen or
                receipt.get('raw_birth') != 'CURRENT_HTTP' or receipt.get('auth') is True
                or receipt.get('status') != 200 or receipt.get('run_id') != ob['run_id']
                or request.get('api') != APIS[security['country']][timeframe]
                or request.get('page') != cursor
                or receipt.get('response_headers', {}).get('cont-yn') != page['continuation']
                or receipt.get('response_headers', {}).get('next-key', '') != page['next_key']):
            raise ValueError('history_page_receipt_binding')
        seen.add(cursor)
        cursor = page['next_key']
        if index < len(root['pages']) and (page['continuation'] != 'Y' or not cursor):
            raise ValueError('history_continuation_chain')
        if digest(parent['raw'].encode()) != page['raw_sha256']:
            raise ValueError('history_raw_hash')
        bodies.append(json.loads(parent['raw'])); receipts.append(receipt)
    parsed, parser_sha = _parsed(bodies, security['country'], timeframe, parser_root, parser_pins)
    cutoff = root['calendar']['session']
    completed = [r for r in parsed if r['date'] <= cutoff and
                 (timeframe == 'daily' or r['date'] < parsed[-1]['date'])]
    if parser_sha != root['parser_sha256'] or completed[-root['requested_rows']:] != root['selected']:
        raise ValueError('history_original_parser_projection')
    return dict(security=deepcopy(security), timeframe=timeframe, rows=deepcopy(root['selected']),
        last_raw_date=parsed[-1]['date'], source_generation=ob['run_id'],
        source_sha256=ob['source_sha'], receipt_sha256=digest(receipts),
        page_sha256=[p['raw_sha256'] for p in root['pages']],
        requested_source_session=cutoff, captured_at=max(p['captured_at'] for p in root['pages']),
        parser_sha256=parser_sha, basis='adjusted_close', source_kind='NATIVE',
        source_exhausted=root['exhausted'], original_status=ob['status'])


def _view(source, calendar_policy=None):
    rows = source['rows']; tf = source['timeframe']; market = source['security']['country']
    session = source['requested_source_session']
    excluded = []
    # A latest US quote is not a settled technical close, even when in range.
    # Earlier native periods are supported by an actually present later row.
    if market == 'US':
        excluded = [r['date'] for r in rows if r['date'] >= source['last_raw_date']]
        rows = [r for r in rows if r['date'] < source['last_raw_date']]
        if tf == 'daily' and rows:
            session = rows[-1]['date']
        elif rows and excluded:
            session = (date.fromisoformat(source['last_raw_date']) - timedelta(days=1)).isoformat()
            from app.services.price_structure_wave_fibonacci_v3_service import _calendar_for_range
            _, cal = _calendar_for_range(market,start=date.fromisoformat(rows[0]['date']),end=date.fromisoformat(session))
            session = str(cal.date_to_session(session,direction='previous').date())
    # The provider's last native period is excluded by the original parser
    # projection. In the opt-in dated view, its presence proves only the prior
    # period; it cannot make the excluded current month complete.
    if calendar_policy is not None and tf != 'daily' and rows:
        last_start = bounds(date.fromisoformat(source['last_raw_date']), tf)[0]
        if bounds(date.fromisoformat(rows[-1]['date']), tf)[0] < last_start:
            limit = min(date.fromisoformat(session), last_start-timedelta(days=1))
            _, cal = calendar_for_range(market, start=date.fromisoformat(rows[0]['date']),
                                        end=limit, policy=calendar_policy)
            session = str(cal.date_to_session(limit, direction='previous').date())
    view = analytic_view(rows, timeframe=tf, market=market, session=session,
                         calendar_policy=calendar_policy)
    view['excluded_latest_unsettled'] = excluded
    return view


class DatedTechnicalOwner:
    """Live, revocable purpose capability; serialized receipts cannot recreate it."""
    def __init__(self, sources, *, parser_root, parser_pins, enabled=False, ttl_seconds=600,
                 clock=time.monotonic, calendar_policy=None):
        if calendar_policy not in (None, CALENDAR_POLICY):
            raise ValueError('history_calendar_policy_unknown')
        roles = sources if isinstance(sources, dict) else {tf: tuple(sources) for tf in TARGETS}
        if (not roles or set(roles)-set(TARGETS) or not 0 < ttl_seconds <= 3600
                or any(not values or any(type(s) not in (LegacyChartReplay, SealedPublicReplay) for s in values)
                       for values in roles.values())):
            raise ValueError('history_backend_sources_or_lifetime')
        self.sources = {tf:tuple(values) for tf,values in roles.items()}
        self.root, self.pins = parser_root, parser_pins
        self.enabled, self.clock, self.expires = enabled, clock, clock() + ttl_seconds
        self.revoked = False; self._receipts = {}; self._source_pins = {}
        self.calendar_policy = calendar_policy

    def revoke(self):
        self.revoked = True

    def issue(self, *, security, timeframe, cutoff, consumer=CONSUMER, use=USE):
        if not self.enabled or self.revoked or self.clock() >= self.expires:
            raise ValueError('history_disabled_expired_or_revoked')
        if consumer != CONSUMER or use != USE or timeframe not in TARGETS:
            raise ValueError('history_consumer_or_use')
        at = datetime.fromisoformat(cutoff)
        if at.tzinfo is None:
            raise ValueError('history_cutoff_timezone')
        sources=[]; views=[]
        for source in self.sources[timeframe]:
            s = (source.replay(security,timeframe) if type(source) is LegacyChartReplay else
                 _public_replay(source,security,timeframe,self.root,self.pins))
            if datetime.fromisoformat(s['captured_at']) > at:
                raise ValueError('history_future_capture')
            sources.append(s); views.append(_view(s, self.calendar_policy))
        key=digest([security,timeframe,cutoff,consumer,use]); source_pin=digest(sources)
        if key in self._source_pins and self._source_pins[key] != source_pin:
            raise ValueError('history_source_changed')
        self._source_pins[key]=source_pin
        # Reuse independent source versions; never overwrite a revised overlap.
        selected=[]; conflicts=[]; admitted=[]
        for s,v in sorted(zip(sources,views),key=lambda pair:pair[0]['captured_at']):
            if not v['rows']:continue
            if selected:
                old={r['date']:r for r in selected}; new={r['date']:r for r in v['rows']}
                overlap=set(old)&set(new)
                changed=sorted(d for d in overlap if old[d] != new[d])
                if not overlap or changed:
                    conflicts.append(dict(source_sha256=s['source_sha256'],changed_dates=changed,
                        reason='REVISED_OVERLAP' if changed else 'NO_VERIFIED_OVERLAP'))
                    continue
                selected=sorted({**old,**new}.values(),key=lambda r:r['date'])
            else:selected=deepcopy(v['rows'])
            admitted.append(s)
        if not selected:
            raise ValueError('history_no_contiguous_qualified_rows')
        effective=selected[-1]['date']
        if timeframe!='daily':
            from app.services.price_structure_wave_fibonacci_v3_service import _calendar_for_range
            start,end=bounds(date.fromisoformat(effective),timeframe)
            _,cal=calendar_for_range(security['country'],start=start,end=end,policy=self.calendar_policy)
            effective=str(cal.sessions_in_range(start,end)[-1].date())
        final=analytic_view(selected,timeframe=timeframe,market=security['country'],session=effective,
                            calendar_policy=self.calendar_policy)
        rows=final['rows'][-TARGETS[timeframe]:]
        annotated=[annotate_normalized_bar(r,provider='kiwoom',market=security['country'],
                    timeframe=timeframe,has_later_chart_row=any(
                        r['date'] < s['last_raw_date'] and r in s['rows'] for s in admitted)) for r in rows]
        features=build_multi_timeframe_feature_packet(ticker=security['ticker'],periods={timeframe:annotated},
            cutoff=date.fromisoformat(effective)).model_dump(mode='json')[timeframe]
        receipt=dict(contract=CONTRACT,consumer=consumer,use=use,security=deepcopy(security),
            timeframe=timeframe,requested_source_sessions=[s['requested_source_session'] for s in sources],
            effective_analysis_as_of=effective,cutoff=cutoff,basis='adjusted_close',source_kind='NATIVE',
            rows=rows,rows_sha256=digest(rows),sources=[{k:v for k,v in s.items() if k!='rows'} for s in sources],
            source_views=[{k:v for k,v in v.items() if k!='rows'} for v in views],
            conflicts=conflicts,features=features,prohibited_uses=list(PROHIBITED),
            current_price=False,strict_native=False,economic_direction=False,send=False)
        if self.calendar_policy is not None:
            receipt['contract'] = 'dated-native-technical-reference-v2'
            receipt['calendar_policy'] = self.calendar_policy
        if key in self._receipts and self._receipts[key] != receipt:
            raise ValueError('history_receipt_changed')
        self._receipts.setdefault(key,receipt)
        return self._receipts[key]

    def consume(self, receipt, *, security, timeframe, cutoff, consumer=CONSUMER, use=USE):
        issued=self.issue(security=security,timeframe=timeframe,cutoff=cutoff,consumer=consumer,use=use)
        if receipt is not issued:
            raise ValueError('history_unissued_or_cross_owner_receipt')
        return deepcopy(issued)

    def references(self, *, security, cutoff):
        """The research prompt receives dated displays, never decision evidence IDs."""
        result=[]
        for tf in sorted(self.sources):
            receipt=self.issue(security=security,timeframe=tf,cutoff=cutoff)
            value=self.consume(receipt,security=security,timeframe=tf,cutoff=cutoff)
            result.append(dict(contract=value['contract'],timeframe=tf,
                effective_analysis_as_of=value['effective_analysis_as_of'],
                available_rows=len(value['rows']),receipt_sha256=digest(value),
                sources=value['sources'],features=value['features'],conflicts=value['conflicts'],
                permitted_slots=['summary','uncertainty'],prohibited_uses=PROHIBITED))
        return result
