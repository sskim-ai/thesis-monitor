"""Bounded append-only release discovery, separate from financial use authority."""
import json
from app.services.vnext_research_store import digest
from app.services.vnext_research_ingestion import AppendResearchStore
from app.services.vnext_incremental_replay import SealedPublicReplay,release_inventory
from app.services.vnext_daily_research import _journal

CONTRACT='bounded-release-watermark-v1'


def observe(config,*,owner=None,seed=None,scope,query=None,observed_at=None):
    """Seed once from sealed identities. Only a new owned snapshot discovers events.

    No network is performed. A receipt-bound snapshot is still not a declaration
    that all later filings were inspected, or that any financial cell is usable.
    """
    if config.environment!='test' or config.mode!='write':raise ValueError('isolated_release_watch_only')
    if not scope.get('provider') or not scope.get('issuer'):raise ValueError('release_issuer_scope_required')
    store=AppendResearchStore(config);key=digest([CONTRACT,scope]);prefix='release-watch-'+key[:24]+'-'
    with store.connect() as c:
        records=[json.loads(r[0]) for r in c.execute('SELECT value FROM research_meta WHERE key LIKE ?',
            ('vnext-runtime-v1:job:'+prefix+'%',))]
    known={e['event_id']:e for r in records for e in r['result']['events']}
    if seed is not None:
        if owner is not None:raise ValueError('seed_is_not_current_discovery')
        events=[dict(e) for e in seed if e['provider']==scope['provider'] and str(e['issuer'])==str(scope['issuer'])]
        result=dict(contract=CONTRACT,events=events,new_events=[],state='HISTORICAL_SEED_CURRENT_NOT_CHECKED',
            scope=scope,financial_use_granted=False,current_discovery='NOT_CHECKED',HTTP=0)
        _journal(store,prefix+'seed',dict(seed_sha256=digest(events)),result)
        return result
    if owner is None:
        return dict(contract=CONTRACT,events=[],new_events=[],state='NOT_CHECKED',scope=scope,
            financial_use_granted=False,current_discovery='NOT_CHECKED',HTTP=0)
    if not any(r['result']['state']=='HISTORICAL_SEED_CURRENT_NOT_CHECKED' for r in records):
        raise ValueError('release_baseline_required_before_new_event_claim')
    if not isinstance(owner,SealedPublicReplay):raise ValueError('owned_release_snapshot_required')
    batch=owner.batch()
    if len(batch['captures'])>8:raise ValueError('bounded_release_snapshot_required_not_historical_sweep')
    discovery=release_inventory(owner)
    events=[e for e in discovery['events'] if e['provider']==scope['provider'] and str(e['issuer'])==str(scope['issuer'])]
    unparsed=[e for e in discovery['unparsed'] if e['provider']==scope['provider']]
    bounded=None
    if query is not None:
        from app.services.vnext_current_parents import opendart_discovery
        bounded=opendart_discovery(owner,scope=scope,query=query,observed_at=observed_at)
    if not events and not unparsed and bounded is None:raise ValueError('release_scope_not_observed')
    result=dict(contract=CONTRACT,scope=scope,events=events,new_events=[e for e in events if e['event_id'] not in known],
        unparsed=unparsed,state='UNCLASSIFIED_DOCUMENTS' if unparsed else 'OWNED_METADATA_SNAPSHOT_OBSERVED',
        current_discovery='BOUNDED_SNAPSHOT_NOT_COMPLETE_CENSUS',financial_use_granted=False,HTTP=0,
        proposed_dirty_roles=['business','valuation'] if any(e['event_id'] not in known for e in events) else [],
        watermark=max((e.get('published') or '' for e in events),default=None))
    if bounded is not None:
        result.update(bounded_query=bounded,state=bounded['state'],current_discovery=bounded['coverage'],
            query_watermark=bounded['query_watermark'],no_new_in_bounded_query=bounded['complete'] and not result['new_events'])
    request=dict(snapshot=owner.pin,scope=scope)
    if bounded is not None:request['bounded_query_sha256']=digest(bounded)
    suffix=owner.pin[:24] if bounded is None else digest(request)[:24]
    # A repeated snapshot reuses its original classification, not a new event.
    with store.connect() as c:
        existing=c.execute('SELECT value FROM research_meta WHERE key=?',
            ('vnext-runtime-v1:job:'+prefix+suffix,)).fetchone()
    if existing:
        return dict(json.loads(existing[0])['result'],new_events=[],proposed_dirty_roles=[],reused_snapshot=True)
    _journal(store,prefix+suffix,request,result)
    return result
