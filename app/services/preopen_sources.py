"""Bounded, read-only incremental observations for the pre-open briefing."""

from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from functools import partial
from math import isfinite
import re
from xml.etree import ElementTree

import httpx

from app.config import get_settings
from app.macro.providers.ecos import EcosProvider
from app.macro.providers.fred import FredProvider
from app.macro.providers.market import completed_market_read_params, normalize_market_observation
from app.models.security import SecurityMaster
from app.providers.filings import OpenDARTProvider, SecEdgarProvider, _dart_keywords
from app.providers.news import GoogleNewsRSSProvider, NaverNewsProvider, clean_text, normalize_title
from app.services.collection_service import _raw_event_to_model
from app.services.event_identity import attribute_claim_actor, event_fingerprint
from app.services.event_relevance_service import EventRelevanceService, extract_structured_flags
from app.services.market_session import NEW_YORK, SEOUL, is_exchange_session_date, preceding_exchange_session_date
from app.services.news_query_service import NewsQueryService
from app.services.unified_run_artifacts import sha256_bytes


US_ETFS = ('SPY', 'QQQ', 'IWM', 'RSP', 'SOXX')
US_MACRO = ('DGS3', 'DGS5', 'DGS10', 'DGS30', 'DCOILWTICO', 'VIXCLS', 'DTWEXBGS', 'BAMLH0A0HYM2')
KR_INDICES = ('KOSPI', 'KOSDAQ')
DART_MATERIAL = {'earnings', 'capital_raise', 'convertible_bond', 'warrant', 'supply_contract',
                 'facility_investment', 'material_management_matter'}
SEC_REPORTS = {'10-Q', '10-K', '20-F'}
SEC_MATERIAL_ITEMS = {'1.01', '1.02', '2.01', '2.02', '2.03', '2.04', '2.05', '2.06',
                      '3.01', '3.02', '4.02', '5.02'}
SEC_REVIEW_FORMS = SEC_REPORTS | {'8-K', '6-K', 'F-1', 'S-1'}
OBSERVATION_LEVELS = ('close', 'value', 'level', 'level_pct', 'price_usd_per_barrel')
READ_SECONDS = 8.0


def _instant(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.utcoffset() is not None else None
    except ValueError:
        return None


def _publication_time(value):
    try:
        parsed = parsedate_to_datetime(value)
        return parsed if parsed.utcoffset() is not None else None
    except (AttributeError, IndexError, TypeError, ValueError):
        return None


def _day(value):
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def _iso(value):
    return value.isoformat() if value is not None else None


def _event_row(provider, event_id, title, url, published_day, published_at, *,
               official, material=False, revision=False):
    return dict(provider=provider, id=event_id, title=title, url=url, official=official,
        material=material, revision=revision, published_date=published_day.isoformat(),
        published_at=_iso(published_at), timestamp_uncertain=published_at is None)


def _window(row, provider, *, at, base_cutoff, zone):
    watermark = ((row.get('preopen') or {}).get('event_watermarks') or {}).get(provider, {})
    checked_at = _instant(watermark.get('requested_at'))
    received = _instant(watermark.get('received_at'))
    query_cutoff = _instant(watermark.get('source_query_cutoff'))
    lower = None
    if watermark.get('status') == 'CHECKED' and checked_at and received and checked_at <= received <= at:
        lower = min(checked_at, query_cutoff) if query_cutoff else checked_at
    today = at.astimezone(zone).date()
    anchor = lower or base_cutoff
    anchor_day = anchor.astimezone(zone).date() if anchor else today - timedelta(days=2)
    wanted = max(3, (today - anchor_day).days + 1)
    return lower, today - timedelta(days=min(wanted, 31)), wanted > 31, set(watermark.get('ids') or ())


def _incremental(candidates, *, lower, base_cutoff, previous, checked, zone):
    # Without a provider watermark, the base cutoff can exclude old headlines
    # from the preview. It cannot establish completed provider coverage.
    boundary = lower or base_cutoff
    if boundary is None:
        return []
    boundary_date = boundary.astimezone(zone).date()
    result, seen, titles = [], set(previous), set()
    for candidate in candidates:
        at = _instant(candidate['published_at'])
        day = date.fromisoformat(candidate['published_date'])
        if candidate['id'] in seen or (at and at > checked):
            continue
        outside_window = at <= boundary if at else day < boundary_date
        if outside_window:
            continue
        title = normalize_title(candidate['title'])
        if not candidate['official'] and title in titles:
            continue
        seen.add(candidate['id'])
        if not candidate['official']:
            titles.add(title)
        confirmed = lower is not None and (at is not None or day > lower.astimezone(zone).date())
        result.append(dict(candidate, incremental='CONFIRMED' if confirmed else 'UNCONFIRMED'))
    return result


async def _news(client, provider, security, universe, *, first, today, settings):
    aliases = NewsQueryService().aliases(security)
    if provider == 'naver_news':
        adapter = NaverNewsProvider(as_of=today, settings=settings)
        response = await client.get(adapter.endpoint,
            params=adapter.request_params(security.ticker, search_aliases=aliases),
            headers={'X-Naver-Client-Id': settings.naver_client_id,
                     'X-Naver-Client-Secret': settings.naver_client_secret})
        response.raise_for_status()
        payload = response.json()
        items = payload['items']
        total = int(payload['total'])
        publications = [(clean_text(item.get('title')), item.get('originallink') or item.get('link'),
                         _publication_time(item.get('pubDate'))) for item in items]
        raw_events = adapter.parse_response(response, ticker=security.ticker)
        capped = total > len(items)
    else:
        adapter = GoogleNewsRSSProvider(as_of=today)
        url = adapter.request_url(security.ticker, (today - first).days, search_aliases=aliases)
        response = await client.get(url)
        response.raise_for_status()
        document = ElementTree.fromstring(response.text)
        if document.find('channel') is None:
            raise ValueError('news_rss_channel_missing')
        items = document.findall('.//item')
        publications = [(clean_text(item.findtext('title')), item.findtext('link'),
                         _publication_time(item.findtext('pubDate'))) for item in items]
        capped = len(items) > adapter.max_items
        raw_events = adapter.parse_response(response, ticker=security.ticker, source_url=url)

    topic = EventRelevanceService()
    by_title_url = {}
    for title, url, at in publications:
        by_title_url.setdefault((title, url), set()).add(at)
    candidates = []
    for raw in raw_events:
        times = by_title_url.get((raw.title, raw.url), set())
        try:
            url = httpx.URL(raw.url)
        except httpx.InvalidURL:
            continue
        if (len(times) != 1 or None in times or url.scheme not in {'http', 'https'}
                or not url.host or url.userinfo):
            continue
        if not topic.validate_against(raw, security, universe).accepted:
            continue
        raw.identity_validated = True
        raw.claim_actor, raw.claim_actor_type = attribute_claim_actor(raw)
        extract_structured_flags(raw)
        event = _raw_event_to_model(raw)
        if event.event_type == 'non_thesis_noise' or not event.requires_review:
            continue
        candidates.append(_event_row(provider, event_fingerprint(event), raw.title, raw.url,
                          raw.date, next(iter(times)), official=False))
    return candidates, publications, capped


async def _dart(client, security, *, first, today, settings):
    response = await OpenDARTProvider().fetch_release_page(client, corp_code=security.corp_code,
        begin=first, end=today, settings=settings)
    payload = response.json()
    if payload['status'] == '013':
        return [], False
    candidates, gap = [], int(payload['total_page']) > 1
    for row in payload['list']:
        receipt = row.get('rcept_no')
        filed = _day(row.get('rcept_dt'))
        title = clean_text(row.get('report_nm'))
        if (row.get('corp_code') != security.corp_code or filed is None
                or not first <= filed <= today
                or not re.fullmatch(r'[0-9]{14}', str(receipt)) or not title):
            gap = True
            continue
        revision = '정정' in title
        important = bool(set(_dart_keywords(title)) & DART_MATERIAL)
        if not important and not revision:
            continue
        candidates.append(_event_row('opendart', receipt, title,
            f'https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt}', filed, None,
            official=True, material=important, revision=revision))
    return candidates, gap


async def _sec(client, security, *, first, today, settings):
    cik = security.cik.zfill(10)
    response = await client.get(SecEdgarProvider.endpoint_template.format(cik=cik),
        headers={'User-Agent': settings.sec_user_agent, 'Accept': 'application/json'})
    response.raise_for_status()
    payload = response.json()
    if str(payload.get('cik', '')).zfill(10) != cik:
        raise ValueError('sec_submission_issuer_mismatch')
    filings = payload['filings']
    recent = filings['recent']
    keys = ('form', 'accessionNumber', 'primaryDocument', 'filingDate')
    columns = [recent[key] for key in keys]
    if not all(isinstance(column, list) for column in columns) or len({len(c) for c in columns}) != 1:
        raise ValueError('sec_submission_parallel_arrays')
    count = len(columns[0])
    times, items = recent.get('acceptanceDateTime', []), recent.get('items', [])
    gap = any((end := _day(old.get('filingTo'))) is None or end >= first for old in filings.get('files', ()))
    candidates = []
    for index, (form, receipt, document, filed) in enumerate(zip(*columns, strict=True)):
        category = str(form).removesuffix('/A')
        if category not in SEC_REVIEW_FORMS:
            continue
        at = _instant(times[index]) if index < len(times) else None
        published = at.astimezone(NEW_YORK).date() if at else _day(filed)
        if published is None:
            gap = True
            continue
        if not first <= published <= today:
            continue
        if (not re.fullmatch(r'[0-9]{10}-[0-9]{2}-[0-9]{6}', str(receipt))
                or not re.fullmatch(r'[A-Za-z0-9_.-]+', str(document)) or document in {'.','..'}):
            gap = True
            continue
        section = {part.strip() for part in str(items[index]).split(',')} if index < len(items) else set()
        material = category in SEC_REPORTS or (category == '8-K' and bool(section & SEC_MATERIAL_ITEMS))
        url = f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{receipt.replace("-", "")}/{document}'
        candidates.append(_event_row('sec_edgar', receipt, str(form), url, published, at,
            official=True, material=material, revision=str(form).endswith('/A')))
    return candidates, gap or (bool(times) and len(times) != count)


def saved_market_rows(display, source):
    """Save original registry-bound display numbers while the accepted plan is in scope."""
    allowed = set((*US_ETFS, *US_MACRO, 'USDKRW') if display.market == 'us' else (*KR_INDICES, 'USDKRW'))
    catalog = {fact['fact_id']: fact for fact in source['fact_catalog']}
    grouped = {}
    for item in display.items:
        if item.status != 'AVAILABLE':
            continue
        for binding in item.bindings:
            fact = catalog[binding.fact_id]
            fields = fact['fields']
            series = fields.get('series_code') or fields.get('symbol') or fields.get('sector_code')
            if series not in allowed:
                continue
            values = grouped.setdefault(fact['fact_id'], {})
            values[binding.field_path.removeprefix('fields.')] = (binding.value, binding.unit)
    results = []
    for fact_id, values in grouped.items():
        fact = catalog[fact_id]
        fields = fact['fields']
        level, unit = next((values[key] for key in OBSERVATION_LEVELS if key in values), (None, None))
        pct = values.get('return_pct', values.get('change_pct', (None, None)))[0]
        bp = values.get('change_bp', (None, None))[0]
        if level is None and pct is None and bp is None:
            continue
        results.append(dict(series=fields.get('series_code') or fields.get('symbol') or fields.get('sector_code'),
            provider=fields.get('provider') or '기존 시장 분석', observed_date=fact['as_of_date'],
            value=level, unit=unit, change_pct=pct, change_bp=bp,
            previous_observed_date=fields.get('previous_observation_date'),
            source_ref=fact_id, source_url=None))
    return results


def _market_row(observation, provider, *, source_ref, prior=None, source_url=None):
    temporal = observation.raw_payload.get('publication_context') or {}
    level, unit = observation.value, observation.unit
    pct, bp = observation.change_pct, None
    prior_date = observation.raw_payload.get('previous_observation_date')
    if prior is not None:
        prior_date = prior.observed_at.date().isoformat()
        if observation.series_code.startswith('DGS') or observation.series_code == 'BAMLH0A0HYM2':
            bp = (level - prior.value) * 100
        elif prior.value > 0:
            pct = (level / prior.value - 1) * 100
    return dict(series=observation.series_code, provider=provider,
        observed_date=temporal.get('observation_date') or observation.observed_at.date().isoformat(),
        value=level, unit=unit, change_pct=pct, change_bp=bp, previous_observed_date=prior_date,
        source_url=source_url, source_ref=source_ref)


async def _etf(client, series, expected, settings):
    headers = {'X-API-Key': settings.ohlcv_api_key or settings.action_api_key}
    response = await client.get(f'{settings.ohlcv_base_url.rstrip("/")}/ohlcv',
        params=completed_market_read_params(series), headers={k: v for k,v in headers.items() if v})
    response.raise_for_status()
    payload = response.json()
    if (payload.get('resolved_symbol', {}).get('code') != series
            or payload.get('meta', {}).get('adjusted') is not True
            or payload.get('meta', {}).get('provider') not in {'ohlcv_analyst', 'kiwoom'}):
        raise ValueError('preopen_market_symbol_or_basis')
    observation = normalize_market_observation(payload, symbol=series, source_url='')
    if observation is None or observation.observed_at.date() != expected:
        raise ValueError('preopen_market_completed_session_mismatch')
    return _market_row(observation, 'ohlcv_analyst', source_ref=sha256_bytes(response.content))


async def _macro(provider, series, zone, clock):
    result = await provider.collect(clock().astimezone(zone))
    available = sorted((row for row in result.observations if row.series_code == series),
                       key=lambda row: row.observed_at)
    if not available:
        raise ValueError('published_market_observation_missing')
    latest = available[-1]
    publication = latest.raw_payload.get('publication_context') or {}
    ref = publication.get('response_sha256')
    if (not publication.get('latest_available_at_query_time') or not publication.get('display_eligible')
            or not ref or not isfinite(latest.value) or (series == 'USDKRW' and latest.value <= 0)):
        raise ValueError('published_market_observation_ineligible')
    return _market_row(latest, provider.name, source_ref=ref,
        prior=available[-2] if len(available) > 1 else None, source_url=latest.source_url)


def _stored_market(run_roots, market, session, as_of):
    root = run_roots.get(market)
    if not root or session is None:
        return {}
    from app.services.preopen_base import read_preopen_base
    base = read_preopen_base(root, market, session, allow_reference=False)
    if not base.is_current or any(at is not None and at > as_of for at in (base.cutoff, base.completed_at)):
        return {}
    market_message = base.messages[0]
    return {row['series']: row for row in market_message.get('preopen_market', ())
            if isinstance(row, dict) and isinstance(row.get('series'), str)
            and (observed := _day(row.get('observed_date'))) is not None and observed <= session}


async def collect_preopen_sources(market, *, opening_session, rows, cutoff, run_roots,
                                  settings=None, base_cutoff=None, enable_network=False,
                                  clock=lambda: datetime.now(timezone.utc), transport=None):
    """Collect a small supplement; each network attempt is optional and deadline-bounded."""
    started = clock()
    if market not in {'kr', 'us'} or any(at.utcoffset() is None for at in
                                       (started, cutoff, *([base_cutoff] if base_cutoff else []))):
        raise ValueError('preopen_source_market_or_time')
    if enable_network and settings is None:
        settings = get_settings()
    rows = tuple(rows)
    zone = SEOUL if market == 'kr' else NEW_YORK
    today = started.astimezone(zone).date()
    result = dict(market=[], events={}, coverage=[], requests={})
    loop = asyncio.get_running_loop()
    end = loop.time() + (cutoff - started).total_seconds()
    throttled = set()

    def cover(topic, provider, status, **details):
        result['coverage'].append(dict(topic=topic, provider=provider, status=status, **details))

    def remaining():
        return min(end - loop.time(), (cutoff - clock()).total_seconds())

    async def read(provider, topic, collect, **details):
        if provider in throttled:
            cover(topic, provider, 'PARTIAL', reason='RATE_LIMITED', **details)
            return None
        if provider == 'sec_edgar' and result['requests'].get(provider):
            if remaining() <= 0.25:
                cover(topic, provider, 'TIMEOUT', **details)
                return None
            await asyncio.sleep(0.25)
        if (seconds := remaining()) <= 0:
            cover(topic, provider, 'TIMEOUT', **details)
            return None
        checked = clock()
        result['requests'][provider] = result['requests'].get(provider, 0) + 1
        try:
            async with asyncio.timeout(min(READ_SECONDS, seconds)):
                value = await collect()
            if remaining() < 0:
                raise TimeoutError
        except (TimeoutError, httpx.TimeoutException):
            cover(topic, provider, 'TIMEOUT', **details)
            return None
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 429:
                throttled.add(provider)
            cover(topic, provider, 'PARTIAL' if status == 429 else 'UNAVAILABLE',
                  reason=f'HTTP_{status}', **details)
            return None
        except (httpx.RequestError, ImportError, ValueError, TypeError, AttributeError, IndexError, KeyError,
                ArithmeticError, ElementTree.ParseError):
            cover(topic, provider, 'UNAVAILABLE', reason='SOURCE_OR_PAYLOAD_UNAVAILABLE', **details)
            return None
        return value, checked, clock()

    expected = preceding_exchange_session_date('XNYS', opening_session) if market == 'kr' else (
        opening_session if is_exchange_session_date('XKRX', opening_session) and today == opening_session else None
    )
    stored = _stored_market(run_roots, 'us' if market == 'kr' else 'kr', expected, started)
    if market == 'kr':
        kr_previous = preceding_exchange_session_date('XKRX', opening_session)
        kr_stored = _stored_market(run_roots, 'kr', kr_previous, started)
        if 'USDKRW' not in stored and 'USDKRW' in kr_stored:
            stored['USDKRW'] = kr_stored['USDKRW']
    targets = {}
    for row in rows:
        metadata = row.get('preopen') or {}
        security = metadata.get('security')
        if isinstance(security, dict) and security.get('ticker') == row.get('ticker') and all(
            security.get(field) for field in ('canonical_company_id', 'canonical_security_id', 'company_name')
        ):
            try:
                targets[row['ticker']] = SecurityMaster.model_validate(security)
            except ValueError:
                pass
    async with AsyncExitStack() as stack:
        client = None
        if enable_network:
            try:
                client = await stack.enter_async_context(httpx.AsyncClient(
                    timeout=READ_SECONDS, follow_redirects=False, transport=transport))
            except (ImportError, OSError, ValueError):
                enable_network = False
                cover('market', 'preopen', 'UNAVAILABLE', reason='NETWORK_CLIENT_UNAVAILABLE')
        series_set = (*US_ETFS, *US_MACRO, 'USDKRW') if market == 'kr' else KR_INDICES
        for series in series_set:
            saved = stored.get(series)
            min_expected = kr_previous if series == 'USDKRW' else expected
            if saved and (_day(saved['observed_date']) == min_expected or
                          (not enable_network and series not in (*US_ETFS, *KR_INDICES))):
                result['market'].append(saved)
                cover('market', saved['provider'], 'SAVED', series=series)
                continue
            provider = ('ohlcv_analyst' if series in US_ETFS else
                        'fred' if series in US_MACRO else 'ecos' if series == 'USDKRW' else 'kr_close')
            collect = None
            if market == 'kr' and enable_network and expected:
                if provider == 'ohlcv_analyst' and settings.ohlcv_base_url:
                    collect = partial(_etf, client, series, expected, settings)
                elif provider == 'fred' and settings.fred_api_key:
                    adapter = FredProvider(transport=transport, series=(series,), clock=clock, settings=settings)
                    collect = partial(_macro, adapter, series, NEW_YORK, clock)
                elif provider == 'ecos' and settings.ecos_api_key:
                    adapter = EcosProvider(transport=transport, clock=clock, settings=settings)
                    collect = partial(_macro, adapter, series, SEOUL, clock)
            if collect:
                observed = await read(provider, 'market', collect, series=series)
                if observed:
                    value, checked, received = observed
                    result['market'].append(value)
                    cover('market', provider, 'OBSERVED', series=series,
                          queried_at=checked.isoformat(), received_at=received.isoformat())
                    continue
            else:
                cover('market', provider, 'UNAVAILABLE' if enable_network else 'DISABLED', series=series,
                      reason='SAVED_ONLY' if market == 'us' else 'NO_CONFIGURED_READ')
            if saved and series not in (*US_ETFS, *KR_INDICES):
                result['market'].append(saved)

        for row in rows:
            ticker = row['ticker']
            target = targets.get(ticker)
            pairs = (('news', 'naver_news'), ('filings', 'opendart')) if market == 'kr' else (
                ('news', 'google_news_rss'), ('filings', 'sec_edgar'))
            for topic, provider in pairs:
                if not enable_network or not target:
                    cover(topic, provider, 'DISABLED' if not enable_network else 'UNAVAILABLE',
                          ticker=ticker, reason='NETWORK_DISABLED' if not enable_network else 'IDENTITY_UNAVAILABLE')
                    continue
                supported = {
                    'naver_news': settings.naver_client_id and settings.naver_client_secret,
                    'google_news_rss': True,
                    'opendart': settings.opendart_api_key and re.fullmatch(r'[0-9]{8}', target.corp_code or ''),
                    'sec_edgar': settings.sec_user_agent and re.fullmatch(r'[0-9]{1,10}', target.cik or ''),
                }
                if not supported[provider]:
                    cover(topic, provider, 'UNAVAILABLE', ticker=ticker, reason='IDENTITY_OR_SETTINGS_UNAVAILABLE')
                    continue
                lower, first, clipped, previous = _window(row, provider, at=started, base_cutoff=base_cutoff, zone=zone)
                if topic == 'news':
                    collect = partial(_news, client, provider, target, targets.values(),
                                      first=first, today=today, settings=settings)
                else:
                    fetch_filing = _dart if market == 'kr' else _sec
                    collect = partial(fetch_filing, client, target, first=first, today=today, settings=settings)
                observed = await read(provider, topic, collect, ticker=ticker)
                if observed is None:
                    continue
                value, checked, received = observed
                if topic == 'news':
                    candidates, publications, capped = value
                    times = [at for _, url, at in publications if at and url]
                    naver_covered = provider == 'naver_news' and lower and times and min(times) <= lower
                    gap = len(times) != len(publications) or (capped and not naver_covered)
                else:
                    candidates, gap = value
                gap = gap or any((at := _instant(event['published_at'])) is not None and at > received
                                 for event in candidates)
                events = _incremental(candidates, lower=lower, base_cutoff=base_cutoff,
                                      previous=previous, checked=received, zone=zone)
                if events:
                    result['events'].setdefault(ticker, []).extend(events)
                material = any(row['material'] and row['incremental'] == 'CONFIRMED' for row in events)
                gap = gap or clipped or lower is None or any(row['incremental'] != 'CONFIRMED' for row in events)
                status = ('PARTIAL' if gap else 'CONFIRMED_CHANGE' if material
                          else 'HEADLINE_REVIEW' if events else 'NO_SIGNIFICANT_CHANGE')
                cover(topic, provider, status, ticker=ticker, queried_at=checked.isoformat(),
                      received_at=received.isoformat(), prior_query_at=_iso(lower),
                      queried_from=first.isoformat(), event_count=len(events), material_change=material)
    cover('quotes', 'premarket', 'UNAVAILABLE', reason='ELIGIBLE_SOURCE_UNVERIFIED')
    cover('market', 'futures', 'UNAVAILABLE', reason='ELIGIBLE_SOURCE_UNVERIFIED')
    return result
