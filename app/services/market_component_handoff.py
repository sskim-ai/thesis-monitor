"""Original component replay -> typed canonical-consumer handoff, not JSON consent."""
from copy import deepcopy
from dataclasses import dataclass
import os
from pathlib import Path
from weakref import WeakKeyDictionary

from app.services.unified_snapshot_contract import digest

CONTRACT='authenticated-market-component-handoff-v1'
_LIVE=WeakKeyDictionary()

class MarketComponentHandoff:
    __slots__=('__weakref__',)

@dataclass(frozen=True)
class MissingMarketParents:
    status:str
    missing:tuple[str,...]
    component_status:str='COMPONENT_SOURCE_OBSERVED'
    MarketParent:str='NOT_ISSUED'


def bind_original_component(*,dispatcher,market,worker_bridge=None,enabled=False):
    from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
    from app.services import current_scoped_source_owner as active,pending_source_parent as pending
    from app.services.current_scoped_source_results import _market
    from app.services.current_scoped_worker_bridge import ScopedBridge
    if enabled is not True or type(dispatcher) is not CurrentScopedDispatcher or market not in ('kr','us'):
        raise ValueError('market_handoff_live_original_dispatch_required')
    dispatcher._require_parent()
    if type(dispatcher._parent) is pending.PendingSourceParent:
        _,spec,_=pending.replay_context(dispatcher._parent)
    else:
        spec=active.ScopedSourceSpec.model_validate_json(active._PARENTS[dispatcher._parent].spec_json)
    commands=None
    if market=='us':
        if (type(worker_bridge) is not ScopedBridge or worker_bridge.transport.dispatcher is not dispatcher
                or worker_bridge.process is None or worker_bridge.process.returncode!=0):
            raise ValueError('market_handoff_original_worker_required')
        commands=worker_bridge.commands
    # Original function verifies sealed child raw pages/wires, normalizes through
    # actual Provider owners and resolves the original transitive aggregate.
    proof=_market(market,spec,dispatcher.plan,dispatcher,dispatcher.root,commands)
    handle=MarketComponentHandoff()
    _LIVE[handle]=dict(dispatcher=dispatcher,market=market,proof=proof,spec=spec,
        commands=deepcopy(commands),pid=os.getpid(),code=digest(Path(__file__).read_bytes().hex()))
    return handle,dict(contract=CONTRACT,status='COMPONENT_SOURCE_OBSERVED',
        component_sha256=proof['component_sha256'],MarketParent='NOT_ISSUED')


def project_original_parent(handle,*,packet,binding,graph,expected_authority_sha256):
    if type(handle) is not MarketComponentHandoff or handle not in _LIVE:
        raise ValueError('market_handoff_unissued_component')
    s=_LIVE[handle];run=s['dispatcher'];run._require_parent()
    if s['pid']!=os.getpid() or s['code']!=digest(Path(__file__).read_bytes().hex()):
        raise ValueError('market_handoff_process_or_code_changed')
    from app.services.current_scoped_source_results import _market
    actual=_market(s['market'],s['spec'],run.plan,run,run.root,s['commands'])
    if actual!=s['proof']:raise ValueError('market_handoff_original_component_changed')
    return _project_complete(packet=packet,binding=binding,graph=graph,market=s['market'],
        component_sha256=actual['component_sha256'],value_sha256=actual['value_sha256'],
        generation_id=run.plan.generation_id,expected_authority_sha256=expected_authority_sha256)


def required_original_parents(packet,binding,graph,market):
    """Exact original graph prerequisites; no fabricated eligible placeholders."""
    from app.services.canonical_market_projection import PUBLICATIONS
    missing=[]
    for name,value in (('packet',packet),('binding',binding),('authority_graph',graph)):
        if not isinstance(value,dict) or not value:missing.append(name)
    if missing:return MissingMarketParents('MISSING_REQUIRED_COMPONENT',tuple(missing))
    for key in ('parent_run_id','started_at','attempts','attempt_hashes','class_c_version_set_sha256','optional_denial_set_sha256'):
        if key not in binding:missing.append('binding.'+key)
    for key in ('run_seed_sha256','class_c','markets','publication_context','optional_denials'):
        if key not in graph:missing.append('graph.'+key)
    if market not in graph.get('markets',{}):missing.append('graph.markets.'+market)
    for role in PUBLICATIONS:
        if 'class-c/'+role+'.json' not in graph.get('publication_context',{}):
            missing.append('original_provider_publication.'+role)
    if market=='us' and 'night' not in graph:missing.append('original_KRX_night_availability_and_receipts')
    return MissingMarketParents('MISSING_REQUIRED_COMPONENT',tuple(missing)) if missing else None


def _project_complete(*,packet,binding,graph,market,component_sha256,value_sha256,generation_id,expected_authority_sha256):
    denial=required_original_parents(packet,binding,graph,market)
    if denial:return denial
    component=graph['markets'][market]['component']
    if (digest(component)!=component_sha256 or component['value_sha256']!=value_sha256
            or graph['markets'][market]['run_id']!=generation_id):
        raise ValueError('market_handoff_exact_authenticated_component_required')
    from app.services.canonical_market_projection import project_production_market_context
    # The original current-run binding and consumer own all remaining session,
    # currency, publication/cutoff, optional-night and source-use checks.
    return project_production_market_context(packet,binding,graph,expected_authority_sha256=expected_authority_sha256)
