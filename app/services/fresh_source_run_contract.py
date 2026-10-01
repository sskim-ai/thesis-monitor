"""R9 pre-dispatch scope and same-generation source guards, not a fact store."""

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.macro.providers.eia import EIA_SERIES
from app.macro.providers.fred import FRED_SERIES
from app.macro.providers.market import MARKET_SYMBOLS
from app.services.bounded_financial_acquisition import make_plan
from app.services.kiwoom_kr_market_context_service import kiwoom_market_reads
from app.services.market_session import korea_market_session
from app.services.night_futures_product_scope import scope_receipt
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import StockPlan
from app.services.unified_stock_owner import reject_downstream

CONTRACT = 'r9-fresh-source-run-v1'
MAX_KR_REQUEST_PAGES = 20
STATIC_TABLES = frozenset({'watchlistitem', 'securitymaster', 'investmentthesis', 'company'})
CURRENT_FORBIDDEN = frozenset({'parent_zip_sha256', 'parent_result_zip', 'versioned_business',
    'versioned_binding', 'accepted_stock_packet', 'old_quality_bundle', 'prior_model_output',
    'old_macro_observation', 'frozen_accepted_reported_comparison', 'persisted_binding'})


def reject_current_carryin(value):
    reject_downstream(value)
    if isinstance(value, dict):
        if CURRENT_FORBIDDEN.intersection(k.lower() for k in value):
            raise ValueError('prior_mutable_source_carryin_forbidden')
        if value.get('contract') in {'frozen-accepted-reported-comparison-input-v1',
                'versioned-business-stock-owner-v1'}:
            raise ValueError('prior_mutable_source_contract_forbidden')
        for child in value.values():
            reject_current_carryin(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            reject_current_carryin(child)
    elif isinstance(value, str):
        import json
        if value.lstrip().startswith(('{', '[')):
            try:
                nested = json.loads(value)
            except ValueError:
                return
            reject_current_carryin(nested)


def validate_local_seed(seed):
    if seed.get('contract') != 'unified-local-seed-projection-v1' or seed.get('denials'):
        raise ValueError('fresh_run_static_seed_ineligible')
    for role in seed['roles'].values():
        for row in role['records']:
            if row['table'] not in STATIC_TABLES:
                raise ValueError('mutable_table_in_static_seed')
    reject_current_carryin(seed)


def _budget(count):
    if type(count) is not int or count < 1:
        raise ValueError('finite_positive_budget_required')
    return dict(maximum_logical=count, maximum_HTTP_attempts=count * 3,
        timeout_seconds=600, transient_retries=2, semantic_retries=0)


def acquisition_plan(stock_plan, identities, *, kr_max_pages, exact_financial_owner=False):
    """Freeze every source class before network. No retained-subject exemption."""
    stock = StockPlan.model_validate(stock_plan)
    if type(kr_max_pages) is not int or not 1 <= kr_max_pages <= MAX_KR_REQUEST_PAGES:
        raise ValueError('finite_kr_page_cap_required')
    universe = stock.universe
    kr_only = set(universe) == {'kr'}
    expected = {t for subjects in universe.values() for t in subjects}
    if set(identities) != expected:
        raise ValueError('exact_22_current_security_identities_required')
    financial = {t: make_plan(identities[t], market=m, cutoff=stock.frozen_at,
        run_id=stock.run_id, all_subjects_fresh=True, exact_financial_owner=exact_financial_owner)
        for m, subjects in universe.items() for t in subjects}
    kr = kiwoom_market_reads(session_date=korea_market_session(stock.frozen_at).latest_completed_regular_session_date,
        max_pages=kr_max_pages, max_requests_per_page=1)
    at = stock.frozen_at.astimezone(ZoneInfo('Asia/Seoul')).date()
    # Current-month DWM plus a bounded prior-month boundary; official missing
    # sessions are preserved, never filled with operating history.
    first = at.replace(day=1) - timedelta(days=7)
    days = [(first + timedelta(days=i)).isoformat() for i in range((at-first).days+1)]
    maxima = dict(stock_wire=sum(r.max_pages for r in stock.reads)+1,
        us_market_wire=len(MARKET_SYMBOLS)*2+4,
        kr_market_wire=sum(r.max_pages for r in kr)+1,
        fred=len(FRED_SERIES), eia=len(EIA_SERIES), ecos=1, night_wire=len(days))
    if kr_only:
        for name in ('us_market_wire', 'fred', 'eia'):
            del maxima[name]
    budgets = {name: _budget(count) for name, count in maxima.items()}
    for ticker, plan in financial.items():
        budgets['financial:'+ticker] = _budget(plan['maximum_logical_requests'])
    result = dict(contract=CONTRACT, run_id=stock.run_id, started_at=stock.frozen_at.isoformat(),
        plan_stage='OFFLINE_CANDIDATE_NOT_QUALIFIED', dispatch_allowed=False,
        stock_plan=stock.model_dump(mode='json'), financial_plans=financial,
        current_subjects=sorted(expected), retained_subjects=[],
        source_identity_sha256=digest(identities), kr_market_reads=[r.model_dump(mode='json') for r in kr],
        us_market_symbols=list(MARKET_SYMBOLS), night_scope=scope_receipt(), night_query_dates=days,
        macro_queries={'fred': {'series': list(FRED_SERIES), 'limit': 5, 'sort_order': 'desc',
                               'observation_end': stock.frozen_at.date().isoformat()},
                       'eia': {'series': list(EIA_SERIES), 'length': 1},
                       'ecos': {'route': 'KeyStatisticList', 'start': 1, 'end': 100, 'period_field': 'TIME'}},
        optional_unavailable={name: {'status': 'OPTIONAL_UNAVAILABLE', 'value': None,
            'reason': 'NO_FRESH_QUALIFIED_OWNER_IN_THIS_PLAN'} for name in
            ('news_and_filing_events', 'earnings_calendar', 'us_exchange_breadth', 'forward_estimates')},
        budgets=budgets, prohibited={k: 0 for k in ('alpha_vantage', 'massive', 'mock', 'fallback',
            'telegram', 'production_db_write', 'scheduler', 'remote_push', 'deploy')})
    if kr_only:
        result.update(scope='KR8_ONLY', us_market_symbols=[],
            macro_queries={'ecos': result['macro_queries']['ecos']})
        result['optional_unavailable'].pop('us_exchange_breadth')
    return {**result, 'plan_sha256': digest(result)}


def validate_fresh_receipt(receipt, *, root, run_id, started_at, cutoff):
    reject_current_carryin(receipt)
    if receipt.get('run_id') != run_id or receipt.get('acquisition_class') != 'FRESH_CURRENT_RUN':
        raise ValueError('current_run_acquisition_required')
    begin, end = (datetime.fromisoformat(receipt[k]) for k in ('requested_at', 'received_at'))
    if any(t.utcoffset() is None for t in (begin, end, started_at, cutoff)) or not started_at <= begin <= end <= cutoff:
        raise ValueError('current_run_receipt_time_mismatch')
    relative = Path(receipt['artifact'])
    root = Path(root).resolve()
    target = root / relative
    if (relative.is_absolute() or '..' in relative.parts or not relative.parts
            or any((root.joinpath(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts)+1))):
        raise ValueError('current_run_artifact_path_invalid')
    from app.services.unified_run_artifacts import sha256_bytes
    if sha256_bytes(target.read_bytes()) != receipt['source_sha256']:
        raise ValueError('current_run_source_hash_mismatch')
    return dict(status='PASS', receipt_sha256=digest(receipt))
