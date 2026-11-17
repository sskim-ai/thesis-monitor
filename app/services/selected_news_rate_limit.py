"""Selected-US optional news absence; never a provider response or business fact."""
from datetime import datetime
import re
from zoneinfo import ZoneInfo

from app.services.unified_snapshot_contract import digest

PROVIDER = 'google_news_rss'
KEY = 'prior_optional_news_rate_limit'
STATUS = 'NEWS_RATE_LIMITED'
NOTICE = '뉴스 자료 미확보: Google News 요청 제한(HTTP 429)으로 이번 실행에서는 조회하지 않았습니다.'
_CUSTODY = {'prior_generation', 'target_session', 'prior_logical_id', 'observed_at',
            'raw_sha256', 'receipt_sha256', 'dispatch_plan_sha256'}


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


def disclose(message, rate_limit_events, *, expected_count):
    bindings = [event.get('binding', {}) for event in rate_limit_events]
    affected = [b for b in bindings if b.get('denial') == STATUS]
    if not affected:
        return message
    if len(affected) != expected_count or any(b.get('provider') != PROVIDER or b.get('evidence') != [] for b in affected):
        raise ValueError('optional_news_render_scope_mismatch')
    text = message['text'].rstrip() + '\n\n' + NOTICE
    if len(text.encode('utf-16-le')) // 2 > 4096:
        raise ValueError('optional_news_render_exceeds_message_limit')
    return {**message, 'text': text, 'content_sha256': digest(text)}
