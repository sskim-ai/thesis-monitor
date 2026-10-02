"""Common-clock synthetic wires, never production source receipts."""
import asyncio
import base64
from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest.mock import patch

import httpx
from sqlmodel import Session, SQLModel, create_engine

from app.models.security import SecurityMaster
from app.providers.news import GoogleNewsRSSProvider
from app.services.unified_event_acquisition import EventAcquisition
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_stock_event_input import BoundNewsInput, PlannedNewsTransport, make_read
from app.services.unified_run_artifacts import sha256_bytes, durable_json
from tests.rev8_source_fixtures import POLICY, fresh_inputs
from tests.test_unified_stock_acquisition import plan as plan_fixture


@contextmanager
def wire_clock(at):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return at.astimezone(tz) if tz else at.replace(tzinfo=None)
    with patch('app.services.bounded_financial_acquisition.datetime', Clock), \
         patch('app.services.unified_event_acquisition.datetime', Clock), \
         patch('app.services.unified_source_observer.datetime', Clock), \
         patch('app.services.unified_kiwoom_observer.datetime', Clock):
        yield


def event_inputs(root, *, persisted=False, current_only=True, future=False, inputs=None):
    if inputs is None:
        plan = plan_fixture.__wrapped__()
        policy = UnifiedSourcePolicy(POLICY.allowed_providers | {'google_news_rss'})
        with wire_clock(plan.frozen_at + timedelta(seconds=4)):
            inputs = fresh_inputs(root / 'financial', 'CORZ', current_only=current_only, policy=policy)
    plan, policy = inputs['technical_inputs']['plan'], inputs['technical_inputs']['policy']
    identity = inputs['financial_inputs']['plan']['security']
    target = SecurityMaster.model_validate(identity)
    records = [target.model_dump(mode='json')]
    original_at = plan.frozen_at - timedelta(hours=1) if persisted else plan.frozen_at + timedelta(seconds=5)
    query = original_at
    publication = original_at + timedelta(hours=1) if future else original_at - timedelta(minutes=1)
    run = 'original-event-run' if persisted else plan.run_id
    market = next(r.market for r in plan.reads if r.subject == target.ticker)
    read = make_read(security=identity, market=market, run_id=run, lookback_days=3, security_records=records)
    title = target.company_name + ' awarded large order supply contract signed'
    body = ('<rss><channel><item><title>' + title + '</title><link>https://example.test/order</link>'
            '<pubDate>' + publication.strftime('%a, %d %b %Y %H:%M:%S GMT') + '</pubDate>'
            '<description>' + target.company_name + ' supply contract signed</description>'
            '<source>Fixture News</source></item></channel></rss>').encode()
    transport = PlannedNewsTransport(read=read, root=root / 'event-wire', policy=policy,
        inner=httpx.MockTransport(lambda r: httpx.Response(200, content=body)))
    engine = create_engine('sqlite://')
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(target)
        session.commit()
        with wire_clock(original_at):
            asyncio.run(EventAcquisition(transport, cutoff=query, max_attempts=1).collect(
                session, GoogleNewsRSSProvider(), target, lookback_days=3, aliases=list(read.aliases)))
    engine.dispose()
    def enc(name):
        return base64.b64encode((transport.root / name).read_bytes()).decode()
    carrier = dict(acquisition_class='PERSISTED_SOURCE_RECHECK' if persisted else 'FRESH_CURRENT_RUN',
        window=inputs.get('source_window') or dict(run_id=plan.run_id, collection_started_at=plan.frozen_at.isoformat(),
            source_query_cutoff=(plan.frozen_at + timedelta(seconds=10)).isoformat(),
            business_availability_cutoff=(plan.frozen_at + timedelta(seconds=30)).isoformat()))
    if persisted:
        from app.services.persisted_business_event_owner import FILES
        assert transport.ordinal == 1
        durable_json(transport.root / 'logical-receipt.json', dict(HTTP_attempts=transport.ordinal,
            logical_attempts=1, owner_error=None, provider=read.provider, subject=target.ticker), exclusive=True)
        carrier['persisted'] = dict(artifacts_b64={name: enc(name) for name in FILES},
            hashes={name: sha256_bytes((transport.root / name).read_bytes()) for name in FILES},
            security_records=records, current_news_denial=dict(role='news_and_filing_events', run_id=plan.run_id,
                acquisition_class='OPTIONAL_UNAVAILABLE', denial='SYNTHETIC_CURRENT_NEWS_UNAVAILABLE'))
    else:
        carrier['source'] = BoundNewsInput(read=read, security_records=tuple(records),
            response_receipt_b64=enc('read-0001.response.json'), normalization_b64=enc('normalization.json'),
            raw_response_b64=enc('read-0001.body')).model_dump(mode='json')
    from app.services.fresh_event_carrier import FreshEventCarrier
    inputs['event_inputs'] = FreshEventCarrier.model_validate(carrier).model_dump(mode='json')
    return inputs


def carrier_owner(inputs):
    from app.services.fresh_event_carrier import replay_carrier
    return replay_carrier(inputs['event_inputs'], plan=inputs['technical_inputs']['plan'], ticker='CORZ',
        security=inputs['financial_inputs']['plan']['security'], policy=inputs['technical_inputs']['policy'])


def source_digest(inputs):
    return digest(inputs['event_inputs'])
