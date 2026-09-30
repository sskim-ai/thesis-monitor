"""Opt-in all-source acquisition. No model, delivery, production write or fallback."""
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from pydantic import TypeAdapter
from sqlmodel import Session, create_engine

from app.macro.providers.base import MacroProviderResult
from app.macro.providers.market import OhlcvMarketProvider
from app.models.security import SecurityMaster
from app.providers.kiwoom_rest_client import KiwoomRestClient
from app.services.bounded_financial_acquisition import collect, SystemicStop
from app.services.fresh_publication_replay import PROVIDERS, public_request
from app.services.kiwoom_kr_market_context_service import KiwoomKrMarketContextService
from app.services.sealed_financial_reader import SealedFinancialReader
from app.services.sealed_fresh_dispatch import consume_bound_result
from app.services.sealed_native_bridge import SealedNativeBridge
from app.services.sealed_source_transport import SealedSourceTransport
from app.services.unified_event_acquisition import EventAcquisition
from app.services.unified_kiwoom_observer import KiwoomRead, KiwoomReceiptObserver
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_source_observer import OhlcvRead, OhlcvReceiptObserver
from app.services.unified_stock_event_input import NewsRead, PlannedNewsTransport, PROVIDERS as NEWS_PROVIDERS


def now():
    return datetime.now(timezone.utc)


class PublicationCapture(httpx.AsyncBaseTransport):
    def __init__(self, sealed, name, run_id, root):
        self.sealed, self.name, self.run_id, self.root = sealed, name, run_id, root
        self.receipts = []
        self.received_at = None

    async def handle_async_request(self, request):
        before = set(self.sealed.dispatcher.results)
        response = await self.sealed.handle_async_request(request)
        new = set(self.sealed.dispatcher.results) - before
        if len(new) != 1:
            raise SourceSafetyStop('publication_exact_dispatch_receipt_required')
        key = new.pop()
        final = self.sealed.dispatcher.results[key]
        last = final['attempts'][-1]
        self.received_at = datetime.fromisoformat(last['finished_at'])
        d = next(d for d in self.sealed.dispatcher.plan.descriptors if d.logical_request_id == key)
        row = dict(run_id=self.run_id, provider=self.name, artifact=d.raw_path if final['status'] == 'PASS' else last.get('artifact'),
            artifact_sha256=sha256_bytes(response.content), requested_at=last['started_at'],
            received_at=last['finished_at'], outcome='HTTP_RESPONSE', http_status=response.status_code,
            request=public_request(request), sealed_logical_id=key, sealed_final_receipt_sha256=final['receipt_sha256'])
        self.receipts.append(row)
        durable_json(self.root / f'receipt-{len(self.receipts):03d}.json', row, exclusive=True)
        return response


async def acquire_all(*, root, frozen, settings, dispatcher, inner, policy, guard):
    """Freeze, then enter once; every HTTP attempt belongs to the one dispatcher."""
    guard()
    durable_json(root / 'live-dispatch-once.json', {'started_at': now().isoformat(),
        'plan_sha256': dispatcher.plan.plan_sha256}, exclusive=True)
    sealed = SealedSourceTransport(dispatcher, inner, providers={d.provider for d in dispatcher.plan.descriptors})
    native_input = root / 'native-input.json'
    durable_json(native_input, {**{k: frozen[k] for k in ('native_owner', 'stock_plan', 'us_market_symbols')},
        'latest_completed_us_session': frozen['sessions']['us']}, exclusive=True)
    bridge = SealedNativeBridge(owner_root=Path(frozen['native_owner_root']), input_path=native_input,
        input_sha256=sha256_bytes(native_input.read_bytes()), output=root/'native', transport=sealed,
        market_reads=frozen['us_market_reads'])
    result = {}
    async def phase(name, action):
        guard()
        try:
            value = await action()
            result[name] = {'status': 'CAPTURED_NOT_QUALIFIED', 'value': value}
        except (SourceSafetyStop, SystemicStop):
            raise
        except Exception as exc:
            # Never archive exception strings that may contain request credentials.
            result[name] = {'status': 'FAILED', 'error_class': type(exc).__name__}
        durable_json(root / ('phase-' + name + '.json'), result[name], exclusive=True)
        print(json.dumps({'phase': name, 'status': result[name]['status']}), flush=True)

    async def us_market():
        await bridge.command({'discovery': True})
        observer = OhlcvReceiptObserver(root=root/'markets/us', run_id=frozen['generation_id'],
            attempt_id=frozen['generation_id']+':us:A1', reads=tuple(OhlcvRead.model_validate(r) for r in frozen['us_market_reads']), policy=policy)
        provider = OhlcvMarketProvider(transport=bridge, source_observer=observer)
        provider.settings = settings
        at = now()
        durable_json(root/'markets/us-query.json', {'observed_at': at.isoformat()}, exclusive=True)
        return TypeAdapter(MacroProviderResult).dump_python(await provider.collect(at), mode='json')

    async def kr_market():
        reads = tuple(KiwoomRead.model_validate(r) for r in frozen['candidate']['kr_market_reads'])
        observer = KiwoomReceiptObserver(root=root/'markets/kr', run_id=frozen['generation_id'],
            attempt_id=frozen['generation_id']+':kr:A1', session_date=datetime.fromisoformat(frozen['sessions']['kr']).date(),
            reads=reads, policy=policy, completed_session_only=True)
        client = KiwoomRestClient(app_key=settings.kiwoom_app_key, secret_key=settings.kiwoom_secret_key,
            base_url=settings.kiwoom_rest_base_url, timeout_seconds=600, max_retries=0,
            request_interval_seconds=settings.kiwoom_rest_request_interval_seconds, transport=sealed, source_observer=observer)
        at = now()
        durable_json(root/'markets/kr-query.json', {'observed_at': at.isoformat()}, exclusive=True)
        try:
            value = await KiwoomKrMarketContextService(client, max_pages=frozen['kr_local_cap'],
                completed_session_only=True).collect(session_date=observer.session_date, observed_at=at)
        except (SourceSafetyStop, SystemicStop):
            raise
        except Exception:
            # Preserve the failed owner's receipt. Independent frozen reads may
            # still be collected, but cannot retroactively qualify that owner.
            client.source_observer = None
            for read in reads:
                key = 'kr_market:'+read.key
                if key in dispatcher.results:
                    continue
                cursor = ''
                for page in range(1, read.max_pages+1):
                    try:
                        response = await client.request(endpoint=read.endpoint, api_id=read.api_id, body=read.body,
                            continuation=page>1, next_key=cursor)
                        if not response.continuation:
                            break
                        cursor = response.next_key
                    except (SourceSafetyStop, SystemicStop):
                        raise
                    except Exception:
                        break
            raise
        return dict(cross_section=value.cross_section.model_dump(mode='json'), audit=value.audit.model_dump(mode='json'))

    async def financial(ticker, plan):
        path = root/'financial'/ticker
        reader = SealedFinancialReader(plan, path, dispatcher=dispatcher, transport=inner, guard=guard,
            api_key=settings.opendart_api_key if plan['market'] == 'kr' else None,
            user_agent=settings.sec_user_agent if plan['market'] == 'us' else None)
        try:
            value = await collect(reader)
        finally:
            durable_json(path/'owner-receipts.json', reader.receipts, exclusive=True)
            durable_json(path/'owner-acquisition.json', reader.output_state, exclusive=True)
        return value

    async def publication(name):
        capture = PublicationCapture(sealed, name, frozen['generation_id'], root/'publications'/name)
        provider = PROVIDERS[name](transport=capture, clock=lambda: capture.received_at)
        provider.settings = settings
        value = await provider.collect(datetime.fromisoformat(frozen['frozen_at']))
        return TypeAdapter(MacroProviderResult).dump_python(value, mode='json')

    async def night():
        from app.jobs.probe_krx_night_futures import fetch_live_probe, KRX_FUTURES_DAILY_URL, USER_AGENT
        from app.macro.providers.krx import materialize_night_probe
        from app.services.krx_night_history_service import persist_krx_response
        capture = PublicationCapture(sealed, 'krx_night_futures', frozen['generation_id'], root/'night/probe')
        at = datetime.fromisoformat(frozen['frozen_at'])
        if now().astimezone(ZoneInfo('Asia/Seoul')).date().isoformat() != frozen['query_kst_date']:
            raise SourceSafetyStop('night_query_day_drift_requires_new_generation')
        probe = await fetch_live_probe(run_date=at.astimezone(ZoneInfo('Asia/Seoul')).date(), observation_time=at,
            api_key=settings.krx_open_api_key, transport=capture, max_lookback_days=7)
        probe.live_source = True
        days = {r['request']['params']['basDd'] for r in capture.receipts}
        earliest = min(days)
        history = PublicationCapture(sealed, 'krx_night_futures', frozen['generation_id'], root/'night/history')
        async with httpx.AsyncClient(transport=history, headers={'AUTH_KEY': settings.krx_open_api_key,
                'User-Agent': USER_AGENT}, timeout=600) as client:
            for day in frozen['candidate']['night_query_dates']:
                if day.replace('-', '') >= earliest:
                    continue
                response = await client.get(KRX_FUTURES_DAILY_URL, params={'basDd': day.replace('-', '')})
                if response.status_code == 200:
                    persist_krx_response(root=root/'night/native-history', query_date=datetime.fromisoformat(day).date(),
                        fetched_at=history.received_at, http_status=200, raw_body=response.content)
        value = TypeAdapter(MacroProviderResult).dump_python(materialize_night_probe(probe, history_directory=root/'night/native-history'), mode='json')
        durable_json(root/'night/query.json', {'observed_at': at.isoformat()}, exclusive=True)
        return value

    async def news(read):
        read = NewsRead.model_validate(read)
        path = root/'events'/read.subject
        transport = PlannedNewsTransport(read=read, root=path, policy=policy, inner=sealed,
            settings_identity=frozen["config_identities"][read.provider])
        provider = NEWS_PROVIDERS[read.market]()
        provider.settings = settings
        at = datetime.fromisoformat(frozen['frozen_at'])
        engine = create_engine('sqlite://')
        SecurityMaster.__table__.create(engine)
        try:
            with Session(engine) as session:
                for raw in frozen['security_records']:
                    session.add(SecurityMaster.model_validate(raw))
                session.commit()
                target = session.get(SecurityMaster, read.security['id'])
                await EventAcquisition(transport, cutoff=at, max_attempts=1).collect(session, provider, target,
                    lookback_days=read.lookback_days, aliases=list(read.aliases))
        finally:
            engine.dispose()
        normalization = json.loads((path/'normalization.json').read_bytes())
        responses = list(path.glob('*.response.json'))
        if len(responses) != 1:
            if transport.pre_dispatch_terminal is not None:
                return dict(status="PRE_DISPATCH_DENIED", terminal=transport.pre_dispatch_terminal)
            raise ValueError('event_exact_response_receipt_required')
        receipt = json.loads(responses[0].read_bytes())
        def b64(p):
            return base64.b64encode(p.read_bytes()).decode()
        source = dict(read=read.model_dump(mode='json'), security_records=frozen['security_records'],
            response_receipt_b64=b64(responses[0]), normalization_b64=b64(path/'normalization.json'),
            raw_response_b64=b64(path/receipt['artifact']) if receipt.get('artifact') else None)
        durable_json(path/'bound-source.json', source, exclusive=True)
        return dict(denial=normalization['denial'], current_run=True)

    try:
        await phase('stocks', lambda: bridge.command({'stocks': True}))
        await phase('us-market', us_market)
        await phase('stock-native-replay', lambda: bridge.command({'replay-stocks': True}))
        await phase('kr-market', kr_market)
        for ticker, plan in frozen['candidate']['financial_plans'].items():
            await phase('financial-'+ticker, lambda t=ticker, p=plan: financial(t, p))
        for name in PROVIDERS:
            await phase(name, lambda n=name: publication(n))
        await phase('night', night)
        for read in frozen['news_reads']:
            await phase('event-'+read['subject'], lambda r=read: news(r))
        if frozen.get('valuation_slots'):
            from app.services.provider_native_valuation_acquisition import collect_native
            await phase('valuation', lambda: collect_native(frozen=frozen, settings=settings, sealed=sealed))
        for key, final in dispatcher.results.items():
            if final['status'] == 'PASS':
                consume_bound_result(root=dispatcher.root, plan=dispatcher.plan, logical_id=key, receipt_sha256=final['receipt_sha256'])
    except (SourceSafetyStop, SystemicStop) as exc:
        result['systemic_stop'] = {'error_class': type(exc).__name__, 'reason': str(exc)}
    finally:
        await bridge.shutdown()
        await sealed.shutdown()
        durable_json(root/'native-exit.json', bridge.exit_receipt, exclusive=True)
        durable_json(root/'acquisition-outcome.json', dict(completed_at=now().isoformat(), phases=result,
            logical_results=dispatcher.results, provider_attempts=sum(len(r['attempts']) for r in dispatcher.results.values()),
            model_calls=0, production_side_effects=0), exclusive=True)
    return result
