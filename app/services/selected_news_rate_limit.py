"""Selected-US optional news absence; never a provider response or business fact."""
from datetime import datetime
import re
from zoneinfo import ZoneInfo

from app.services.unified_snapshot_contract import digest

PROVIDER = 'google_news_rss'
KEY = 'prior_optional_news_rate_limit'
STATUS = 'NEWS_RATE_LIMITED'
NOTICE = '뉴스 자료 미확보: Google News 요청 제한(HTTP 429).'
_CUSTODY = {'prior_generation', 'target_session', 'prior_logical_id', 'observed_at',
            'raw_sha256', 'receipt_sha256', 'dispatch_plan_sha256'}


def optional_scope(plan, descriptor):
    from app.services.selected_source_plan import SelectedRequestPlan
    from app.services.unified_stock_acquisition import UNIVERSE
    d = descriptor
    if (type(plan) is SelectedRequestPlan and plan.market == 'us' and d.market == 'us'
            and d.subject in UNIVERSE['us'] and d.subject in plan.subjects
            and d.provider == PROVIDER and d.mandatory is False
            and d.consumer_role not in plan.mandatory_roles and d.endpoint_operation == 'news'
            and d.logical_request_id == d.consumer_role == 'events:' + d.subject
            and d.max_transport_attempts == 1 and d.transient_retry_max == 0):
        return dict(logical_id=d.logical_request_id, mandatory=False, operation='news',
            plan_sha256=plan.plan_sha256, descriptor_sha256=d.descriptor_sha256)
    return None


def require_current(proof, *, generation, session, started_at, completed_at):
    fields = (_CUSTODY - {'prior_generation', 'prior_logical_id'}) | {'generation_id', 'logical_id'}
    if (not isinstance(proof, dict) or set(proof) != fields | {'provider', 'http_status'}
            or proof['provider'] != PROVIDER or proof['http_status'] != 429
            or proof['generation_id'] != generation or proof['target_session'] != session
            or not proof['logical_id'].startswith('events:')
            or any(not re.fullmatch('[a-f0-9]{64}', proof[k])
                   for k in ('raw_sha256', 'receipt_sha256', 'dispatch_plan_sha256'))):
        raise ValueError('optional_news_current_429_binding_invalid')
    observed = datetime.fromisoformat(proof['observed_at'])
    if observed.utcoffset() is None or not started_at <= observed <= completed_at:
        raise ValueError('optional_news_current_429_outside_collection')


def current_rows(root, frozen, plan, results):
    from pathlib import Path
    from app.services.campaign_runtime_cap import OPTIONAL_NEWS_429
    from app.services.unified_run_artifacts import sha256_bytes

    if frozen.get('optional_news_429') != OPTIONAL_NEWS_429:
        return {}
    if KEY in frozen:
        skipped_slots(frozen, plan)
        if any(k.startswith('events:') for k in results):
            raise ValueError('optional_news_prior_skip_has_current_wire')
        return {}
    qualified = {d.logical_request_id: d for d in plan.descriptors if optional_scope(plan, d)}
    failed = [(qualified[k], r) for k, r in results.items() if k in qualified
              and any(a.get('status') == 429 for a in r.get('attempts', []))]
    if not failed:
        return {}
    if len(failed) != 1:
        raise ValueError('optional_news_multiple_429_after_latch')
    d, final = failed[0]
    attempts = final.get('attempts', [])
    root = Path(root)
    if (len(attempts) != 1 or final.get('status') != 'FAILED'
            or final.get('generation_id') != plan.generation_id
            or final.get('logical_request_id') != d.logical_request_id
            or final.get('descriptor_sha256') != d.descriptor_sha256
            or final.get('plan_sha256') != plan.plan_sha256
            or final.get('receipt_sha256') != digest({k: v for k, v in final.items() if k != 'receipt_sha256'})
            or attempts[0].get('status') != 429 or attempts[0].get('error') is not None
            or attempts[0].get('retry') is not False
            or json_read(root/'dispatch/receipts'/d.logical_request_id/'final.json') != final):
        raise ValueError('optional_news_current_original_receipt_invalid')
    a = attempts[0]
    body = root/'dispatch'/a['artifact']
    if (not body.resolve().is_relative_to((root/'dispatch').resolve()) or body.is_symlink()
            or sha256_bytes(body.read_bytes()) != a['raw_sha256']):
        raise ValueError('optional_news_current_raw_hash_mismatch')
    proof = dict(provider=PROVIDER, http_status=429, generation_id=plan.generation_id,
        target_session=frozen['sessions']['us'], logical_id=d.logical_request_id,
        observed_at=a['finished_at'], raw_sha256=a['raw_sha256'],
        receipt_sha256=final['receipt_sha256'], dispatch_plan_sha256=plan.plan_sha256)
    require_current(proof, generation=plan.generation_id, session=frozen['sessions']['us'],
        started_at=plan.frozen_at, completed_at=datetime.fromisoformat(a['finished_at']))
    ordered = [r['subject'] for r in frozen['news_reads']]
    affected = ordered[ordered.index(d.subject):]
    if any('events:' + t in results for t in affected if t != d.subject):
        raise ValueError('optional_news_wire_after_latch')
    return {t: current_row(proof, t) for t in affected}


def json_read(path):
    import json
    if path.is_symlink():
        raise ValueError('optional_news_receipt_symlink')
    return json.loads(path.read_bytes())


def current_row(proof, ticker):
    attempted = proof['logical_id'] == 'events:' + ticker
    return dict(status=STATUS, disposition='OPTIONAL_HTTP_429' if attempted else 'SKIPPED_RATE_LIMIT',
        wire_attempts=int(attempted), generation_id=proof['generation_id'], subject=ticker, current=proof)


def replay_current(row, *, frozen, plan, outcome, ticker, root, window):
    expected = current_rows(root, frozen, plan, outcome['logical_results']).get(ticker)
    if (row != expected or expected is None
            or outcome['phases'].get('event-' + ticker) != {'status': 'CAPTURED_NOT_QUALIFIED', 'value': row}
            or not row['wire_attempts'] and ((root/'events'/ticker).exists()
                or (root/'dispatch/receipts'/('events:' + ticker)).exists())):
        raise ValueError('optional_news_current_skip_unsealed_or_has_wire')
    require_current(row['current'], generation=plan.generation_id, session=frozen['sessions']['us'],
        started_at=plan.frozen_at, completed_at=datetime.fromisoformat(outcome['completed_at']))
    return dict(acquisition_class='OPTIONAL_NEWS_RATE_LIMITED', window=window, rate_limit=row)


def require_prior(proof, *, generation, session, started_at):
    if (not isinstance(proof, dict) or set(proof) != _CUSTODY | {'provider', 'http_status'}
            or proof['provider'] != PROVIDER or proof['http_status'] != 429
            or proof['prior_generation'] == generation or not proof['prior_generation']
            or proof['target_session'] != session or not proof['prior_logical_id'].startswith('events:')
            or any(not re.fullmatch(r'[0-9a-f]{64}', proof[k])
                   for k in ('raw_sha256', 'receipt_sha256', 'dispatch_plan_sha256'))):
        raise ValueError('optional_news_original_429_binding_invalid')
    observed = datetime.fromisoformat(proof['observed_at'])
    kst = ZoneInfo('Asia/Seoul')
    if (observed.utcoffset() is None or started_at.utcoffset() is None or observed >= started_at
            or observed.astimezone(kst).date() != started_at.astimezone(kst).date()):
        raise ValueError('optional_news_429_outside_same_day_prior_generation')


def skipped_slots(frozen, plan):
    if KEY not in frozen:
        return {}
    from app.services.production_source_consumer import consumer_policy
    from app.services.unified_stock_acquisition import UNIVERSE

    proof = frozen[KEY]
    session = frozen['sessions']['us']
    require_prior(proof, generation=plan.generation_id, session=session, started_at=plan.frozen_at)
    subjects = set(UNIVERSE['us'])
    news = {d.logical_request_id: d for d in plan.descriptors if d.provider == PROVIDER}
    policy = consumer_policy(market='us', session=session, code_config_sha256=digest('optional-news-role-check'))
    if (frozen.get('scope') != 'SELECTED_ORIGINAL_RESEARCH_V1' or plan.market != 'us'
            or frozen.get('selected_market') != 'us' or set(plan.subjects) != subjects
            or set(news) != {'events:' + t for t in subjects} or proof['prior_logical_id'] not in news
            or any(r.required and (r.role.provider == PROVIDER or r.role.key in news) for r in policy.source_roles)
            or any(d.mandatory or d.consumer_role in plan.mandatory_roles or d.market != 'us'
                   or d.max_transport_attempts != 1 or d.consumer_role != key
                   or d.endpoint_operation != 'news' or key != 'events:' + d.subject for key, d in news.items())):
        raise ValueError('optional_news_original_role_not_optional')
    return {d.subject: dict(status=STATUS, disposition='SKIPPED_RATE_LIMIT', wire_attempts=0,
                            generation_id=plan.generation_id, subject=d.subject, prior=proof)
            for d in news.values()}


def replay_skip(row, *, frozen, plan, outcome, ticker, root, window):
    key = 'events:' + ticker
    if (row != skipped_slots(frozen, plan).get(ticker)
            or outcome['phases'].get('event-' + ticker) != {'status': 'CAPTURED_NOT_QUALIFIED', 'value': row}
            or key in outcome['logical_results'] or (root/'dispatch/receipts'/key).exists()
            or (root/'events'/ticker).exists()):
        raise ValueError('optional_news_skip_unsealed_or_has_wire_result')
    return dict(acquisition_class='OPTIONAL_NEWS_RATE_LIMITED', window=window, rate_limit=row)


def disclose(message, rate_limit_events, *, expected_count, allow_partition=False):
    bindings = [event.get('binding', {}) for event in rate_limit_events]
    affected = [b for b in bindings if b.get('denial') == STATUS]
    if not affected:
        return message
    subjects = [b.get('rate_limit', {}).get('subject') for b in affected]
    if (len(bindings) != expected_count or len(affected) > expected_count
            or len(set(subjects)) != len(subjects) or None in subjects
            or any(b.get('provider') != PROVIDER or b.get('evidence') != [] for b in affected)):
        raise ValueError('optional_news_render_scope_mismatch')
    notice = NOTICE + (' 대상: ' + ', '.join(subjects) if expected_count > 1 else '')
    text = message['text'].rstrip() + '\n\n' + notice
    if not allow_partition and len(text.encode('utf-16-le')) // 2 > 4096:
        raise ValueError('optional_news_render_exceeds_message_limit')
    return {**message, 'text': text, 'content_sha256': digest(text)}
