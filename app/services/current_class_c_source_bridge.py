"""Opt-in, process-local Class-C handoff. Membership is not source-use authority.

Only the trusted producer may pass live capture/Owner capabilities here. This
module neither reads a database nor records approval nor admits a dispatcher.
"""
from copy import deepcopy
from datetime import datetime
import json
import os
from pathlib import Path
from weakref import WeakKeyDictionary

from app.services.minimal_class_c_export import captured_private_snapshot, project_captured_export
from app.services.prospective_class_c_owner import SCOPE, apply_prospective_owner, require_generation
from app.services.unified_local_seed_bridge import admit_pinned_local_seed
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_stock_acquisition import StockPlan, UNIVERSE, make_reads

CONTRACT = 'live-class-c-source-bridge-v1'


class CurrentClassCBridge:
    __slots__ = ('__weakref__',)


_LIVE = WeakKeyDictionary()


def _code():
    return sha256_bytes(Path(__file__).read_bytes())


def _state(handle):
    if type(handle) is not CurrentClassCBridge or handle not in _LIVE:
        raise ValueError('class_c_live_bridge_required')
    s = _LIVE[handle]
    if s['pid'] != os.getpid() or s['code'] != _code():
        raise ValueError('class_c_bridge_process_or_code_changed')
    raw, receipt = captured_private_snapshot(s['capture'])
    if sha256_bytes(raw) != s['capture_sha'] or digest(receipt) != s['receipt_sha']:
        raise ValueError('class_c_bridge_capture_changed')
    for owner in s['owners'].values():
        require_generation(owner, s['stock'].run_id, purpose=SCOPE)
    return s


def prepare_current_bridge(*, capture, owners, policy, stock_metadata, counts,
                           config_identities, configured_kr_pages,
                           kr_post_acquisition_completeness_approved, enabled=False):
    """Build the original full-cohort plans from an already approved capture.

    The returned plans are proposals only. Original dispatcher admission and
    collection, financial, publication and economic gates remain mandatory.
    """
    if enabled is not True:
        raise ValueError('class_c_bridge_default_off')
    if set(owners) != set(UNIVERSE):
        raise ValueError('class_c_bridge_exact_market_owners_required')
    raw, receipt = captured_private_snapshot(capture)
    at = datetime.fromisoformat(receipt['cutoff'])
    required = {'run_id', 'acquisition_id', 'instruction_sha', 'implementation_sha',
                'owner_files', 'owner_head', 'settings_sha256', 'request_environment_sha256'}
    if set(stock_metadata) != required:
        raise ValueError('class_c_bridge_stock_metadata_scope')
    from app.services.prospective_class_c_owner import completed_clock
    projections, identities, sessions = {}, {}, {}
    for market, subjects in UNIVERSE.items():
        require_generation(owners[market], stock_metadata['run_id'], purpose=SCOPE)
        sessions[market] = completed_clock(market, at)['target']
        original = project_captured_export(capture, market=market, session_key=sessions[market], policy=policy)
        doc = apply_prospective_owner(original, original=original, owner=owners[market])
        if tuple(sorted(doc['universe']['eligible_subjects'])) != subjects:
            raise ValueError('class_c_bridge_original_cohort_mismatch')
        if doc['denials'] or not all(r['eligible'] for r in doc['roles'].values()):
            raise ValueError('class_c_bridge_original_role_denied')
        projections[market] = doc
        for component in doc['roles'].values():
            for row in component['records']:
                if row['table'] == 'securitymaster':
                    record = row['record']
                    ticker = record['ticker']
                    if ticker in identities and identities[ticker] != record:
                        raise ValueError('class_c_bridge_conflicting_security_identity')
                    identities[ticker] = record
    universe = {m: d['universe'] for m, d in projections.items()}
    stock = StockPlan(**deepcopy(stock_metadata), frozen_at=at, universe_sha256=digest(universe),
        reads=make_reads(universe, identities, at=at, counts=counts))
    if any(r.latest_completed_session != sessions[r.market] for r in stock.reads):
        raise ValueError('class_c_bridge_original_calendar_disagreement')
    from app.services.unified_stock_event_input import make_read
    from app.services.canonical_source_plan import compile_slots
    records = list(identities.values())
    news = [make_read(security=s, market='kr' if s['country'] == 'KR' else 'us',
        run_id=stock.run_id, lookback_days=3, security_records=records) for s in records]
    compiled = compile_slots(stock=stock, identities=identities, news_reads=news,
        config_identities=config_identities, configured_kr_pages=configured_kr_pages,
        kr_post_acquisition_completeness_approved=kr_post_acquisition_completeness_approved,
        exact_financial_owner=True)
    frozen = dict(generation_id=stock.run_id, frozen_at=at.isoformat(), execution_purpose=SCOPE,
        sessions=sessions, stock_plan=stock.model_dump(mode='json'),
        plan=compiled['plan'].model_dump(mode='json'), candidate=compiled['candidate'],
        protected_input_hashes={f'class-c/local-{m}.json': digest(d) for m, d in projections.items()},
        class_c_storage=CONTRACT, capture_sha256=sha256_bytes(raw),
        capture_receipt_sha256=digest(receipt), bridge_code_sha256=_code(),
        acquisition_fragment_not_source_qualification=True)
    handle = CurrentClassCBridge()
    _LIVE[handle] = dict(pid=os.getpid(), code=_code(), capture=capture, capture_sha=sha256_bytes(raw),
        receipt_sha=digest(receipt), owners=dict(owners), policy=digest(sorted(policy.allowed_providers)),
        projections={m: encoded(d) for m, d in projections.items()},
        stock=StockPlan.model_validate_json(stock.model_dump_json()),
        compiled=compiled, frozen=deepcopy(frozen), dispatcher=None, root=None)
    return handle, stock, deepcopy(frozen)


def _require(handle, frozen, plan, policy):
    s = _state(handle)
    if (frozen != s['frozen'] or plan.model_dump(mode='json') != s['stock'].model_dump(mode='json')
            or digest(sorted(policy.allowed_providers)) != s['policy']):
        raise ValueError('class_c_bridge_frozen_contract_mismatch')
    return s


def memory_local_seed(handle, *, frozen, plan, market, policy):
    s = _require(handle, frozen, plan, policy)
    if market not in s['projections']:
        raise ValueError('class_c_bridge_market_scope')
    return admit_pinned_local_seed(s['projections'][market],
        expected_sha256=frozen['protected_input_hashes'][f'class-c/local-{market}.json'],
        market=market, session_key=frozen['sessions'][market], cutoff=plan.frozen_at,
        subjects=plan.universe[market], policy=policy, prospective_owner=s['owners'][market])


def memory_owners(handle):
    return dict(_state(handle)['owners'])


def memory_version_set(handle, *, frozen, policy):
    s = _state(handle)
    return {f'class-c/local-{m}.json': sha256_bytes(encoded(memory_local_seed(handle,
        frozen=frozen, plan=s['stock'], market=m, policy=policy)) + b'\n') for m in s['owners']}


def bind_existing_dispatcher(handle, dispatcher, *, policy):
    """Trusted call-site binding, not a replacement for dispatcher admission.

    A prospective membership grant cannot invoke the production-only dispatcher.
    This bridge does not issue the existing proof-plan authority either.
    """
    from app.services.sealed_fresh_dispatch import RequestPlan, SealedDispatcher
    s = _state(handle)
    if type(dispatcher) is not SealedDispatcher:
        raise ValueError('class_c_bridge_original_manual_dispatcher_required')
    base = {k: dispatcher.plan.model_dump(mode='json')[k] for k in RequestPlan.model_fields}
    if base != s['compiled']['plan'].model_dump(mode='json'):
        raise ValueError('class_c_bridge_dispatch_plan_mismatch')
    if (not dispatcher.admission.get('live_dispatch_allowed') or dispatcher.halted
            or dispatcher.admission.get('plan_sha256') != dispatcher.plan.plan_sha256):
        raise ValueError('class_c_bridge_dispatch_not_admitted')
    root = dispatcher.root.parent
    if dispatcher.root.name != 'dispatch' or any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError('class_c_bridge_dispatch_root_mismatch')
    if s['dispatcher'] is not None:
        if s['dispatcher'] is not dispatcher:
            raise ValueError('class_c_bridge_dispatcher_replacement_denied')
        return deepcopy(s['frozen'])
    if dispatcher.used or dispatcher.results:
        raise ValueError('class_c_bridge_bind_before_dispatch_required')
    _require(handle, s['frozen'], s['stock'], policy)
    s['frozen']['plan'] = dispatcher.plan.model_dump(mode='json')
    s['dispatcher'], s['root'] = dispatcher, root
    return deepcopy(s['frozen'])


def require_dispatch(handle, *, root, frozen, policy):
    s = _require(handle, frozen, StockPlan.model_validate(frozen['stock_plan']), policy)
    dispatcher = s['dispatcher']
    if (dispatcher is None or Path(root) != s['root'] or dispatcher.halted
            or dispatcher.root != s['root']/'dispatch'):
        raise ValueError('class_c_bridge_bound_dispatcher_required')
    paths = (dispatcher.root/'plan.json', dispatcher.root/'admission.json')
    if any(p.is_symlink() for path in paths for p in (path, *path.parents)):
        raise ValueError('class_c_bridge_dispatch_symlink_denied')
    if (dispatcher.plan.model_dump(mode='json') != frozen['plan']
            or json.loads((dispatcher.root/'plan.json').read_bytes()) != frozen['plan']
            or json.loads((dispatcher.root/'admission.json').read_bytes()) != dispatcher.admission):
        raise ValueError('class_c_bridge_dispatch_seal_changed')
    return dispatcher


def publication_capture(handle, *, root, frozen, policy, provider, inner, night_role=None):
    import httpx
    from app.services.canonical_source_acquisition import PublicationCapture
    from app.services.sealed_source_transport import SealedSourceTransport
    dispatcher = require_dispatch(handle, root=root, frozen=frozen, policy=policy)
    if provider not in {'fred', 'eia', 'ecos', 'krx_night_futures'}:
        raise ValueError('class_c_bridge_publication_provider_denied')
    if provider == 'krx_night_futures':
        if night_role not in {'probe', 'history'}:
            raise ValueError('class_c_bridge_night_role_required')
        destination = root/'night'/night_role
    else:
        if night_role is not None:
            raise ValueError('class_c_bridge_unexpected_night_role')
        destination = root/'publications'/provider
    class GuardedAttempt(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            from app.services.unified_live_source_transport import SourceSafetyStop
            def guard():
                try:
                    require_dispatch(handle, root=root, frozen=frozen, policy=policy)
                except (ValueError, OSError):
                    raise SourceSafetyStop('class_c_bridge_attempt_authority_lost') from None
            guard()
            response = await inner.handle_async_request(request)
            try:
                guard()
            except BaseException:
                await response.aclose()
                raise
            return response
        async def aclose(self):
            await inner.aclose()
    class GuardedTransport(SealedSourceTransport):
        async def handle_async_request(self, request):
            require_dispatch(handle, root=root, frozen=frozen, policy=policy)
            response = await super().handle_async_request(request)
            require_dispatch(handle, root=root, frozen=frozen, policy=policy)
            return response
    sealed = GuardedTransport(dispatcher, GuardedAttempt(), providers={provider})
    return PublicationCapture(sealed, provider, frozen['generation_id'], destination)


def revoke_bridge(handle):
    if type(handle) is not CurrentClassCBridge or handle not in _LIVE:
        raise ValueError('class_c_live_bridge_required')
    del _LIVE[handle]
