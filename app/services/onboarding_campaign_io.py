"""Opt-in cost accounting over original onboarding services, not source authority."""
from collections import Counter
from contextlib import contextmanager

from sqlalchemy import event
from sqlalchemy.sql import Select

from app.services.collection_service import CollectionService
from app.services.ohlcv_client import OhlcvClient
from app.services.valuation_snapshot_service import ValuationSnapshotService


class InitialEvidenceIO:
    def __init__(self, *, ledger, direct_transport, ohlcv_transport,
                 require_ohlcv_physical_binding):
        self.ledger = ledger
        self.direct_transport = direct_transport
        self.ohlcv_transport = ohlcv_transport
        self.require_ohlcv_physical_binding = require_ohlcv_physical_binding

    @classmethod
    def for_runtime_campaign(cls,*,ledger,market,subject,direct_inner=None,ohlcv_inner=None):
        from app.services.campaign_runtime_cap import MeteredAsyncTransport,CampaignOhlcvTransport
        binding=ledger.worker_binding()
        ohlcv=CampaignOhlcvTransport(binding=binding,market=market,subject=subject,inner=ohlcv_inner)
        direct=MeteredAsyncTransport(binding=binding,market=market,subject=subject,
            phase='ONBOARDING',owner='OriginalOnboardingProviders',inner=direct_inner)
        return cls(ledger=ledger,direct_transport=direct,ohlcv_transport=ohlcv,
            require_ohlcv_physical_binding=ohlcv.require_binding)

    async def build_evidence(self, session, item, **kwargs):
        from app.services.onboarding_evidence_service import build_initial_evidence
        return await build_initial_evidence(session,item,campaign_io=self,**kwargs)

    async def populate_profile(self, session, item, *, current, data_dir):
        from app.config import get_settings
        from app.services.company_profile_service import (
            CompanyProfilePopulationService, OpenDartCompanyProfileSource, SecCompanyProfileSource,
        )
        settings = get_settings()
        if self.direct_transport is None:
            raise ValueError('campaign_profile_physical_dispatch_unbound')
        service = CompanyProfilePopulationService(data_dir=data_dir,
            kr_source=OpenDartCompanyProfileSource(settings.opendart_api_key,transport=self.direct_transport),
            us_source=SecCompanyProfileSource(settings.sec_user_agent,transport=self.direct_transport))
        return await service.populate_items(session,[item],verified_at=current)

    def initial_services(self, item):
        subjects = {t for child in self.ledger.identity['children'].values() for t in child['subjects']}
        if item.ticker not in subjects or self.direct_transport is None or self.ohlcv_transport is None:
            raise ValueError('campaign_initial_evidence_egress_unbound')
        if self.require_ohlcv_physical_binding is None:
            raise ValueError('campaign_ohlcv_lower_physical_dispatch_unbound')
        # A counted localhost GET cannot stand in for its Kiwoom HTTP attempts.
        self.require_ohlcv_physical_binding(self.ledger, item.ticker)
        return (CollectionService(campaign_transport=self.direct_transport,
                campaign_provider_names=('sec_edgar','opendart','google_news_rss','naver_news')
                if self.ledger.identity.get('runtime_cap') else None),
            OhlcvClient(transport=self.ohlcv_transport, campaign_no_retry=True),
            ValuationSnapshotService(transport=self.direct_transport))


@contextmanager
def onboarding_database_budget(session, ledger):
    """Count attempted ORM rows, SELECT statements and commits before dispatch.

    Only the caller's already authorized Session is instrumented. No connection
    is opened here. Raw/bulk writes and unscoped model rows are refused rather
    than guessed safe. Existing intermediate commits are deliberately retained.
    """
    if not ledger.identity.get('database_budget'):
        raise ValueError('campaign_database_budget_not_frozen')
    if session.new or session.dirty or session.deleted or session.in_transaction():
        raise ValueError('campaign_clean_unused_session_required')
    subjects = {t for c in ledger.identity['children'].values() for t in c['subjects']}
    pending = Counter()
    engine = session.get_bind()
    connections = set()

    def begin(s, transaction, connection):
        connections.add(connection)

    def flush(s, context, instances):
        if s.deleted:
            raise ValueError('campaign_database_delete_forbidden')
        for operation, rows in (('INSERT', s.new), ('UPDATE', s.dirty)):
            for row in rows:
                if operation == 'UPDATE' and not s.is_modified(row, include_collections=False):
                    continue
                if getattr(row, 'ticker', None) not in subjects:
                    raise ValueError('campaign_database_other_subject_forbidden')
                key = operation+':'+row.__tablename__
                ledger.before_onboarding_database(key)
                pending[key] += 1

    def execute(connection, cursor, statement, parameters, context, executemany):
        if connection not in connections:
            return
        compiled = context.compiled
        value = compiled.statement if compiled is not None else None
        if isinstance(value, Select):
            ledger.before_onboarding_database('SELECT')
            return
        operation = 'INSERT' if getattr(value, 'is_insert', False) else 'UPDATE' if getattr(value, 'is_update', False) else None
        if operation is None:
            raise ValueError('campaign_database_raw_bulk_or_schema_forbidden')
        key = operation+':'+value.table.name
        if not session._flushing or pending[key] < 1:
            raise ValueError('campaign_database_unscoped_write_forbidden')

    def commit(s):
        ledger.before_onboarding_database('COMMIT')

    def clear(s, *args):
        pending.clear()

    listeners = [(session,'after_begin',begin), (session,'before_flush',flush),
        (session,'before_commit',commit), (session,'after_rollback',clear),
        (session,'after_flush_postexec',clear),
        (engine,'before_cursor_execute',execute)]
    for target, name, callback in listeners:
        event.listen(target,name,callback)
    try:
        yield
    finally:
        for target, name, callback in reversed(listeners):
            event.remove(target,name,callback)
