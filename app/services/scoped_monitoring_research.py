"""Explicit per-market research composition through original subject/market owners.

This is not a Source-only promotion or an alternate Full22 acquisition policy.
Existing registration capabilities and original preflights remain mandatory.
"""
from copy import deepcopy
import os

from app.services import canonical_native_source_owner as original
from app.services import prospective_class_c_owner as registration
from app.services.canonical_market_projection import project_production_market_context
from app.services.canonical_monitoring_source import prepare_monitoring_source
from app.services.direction_timing_ownership_service import verified_owned_packet_view
from app.services.model_execution_plan import CohortSubject, FrozenCohort, _instant
from app.services.unified_snapshot_contract import digest

CONTRACT = 'scoped-original-monitoring-research-v1'


class ScopedPreparedResearchOwner(original.CanonicalPreparedSourceOwner):
    def _record(self):
        row = super()._record()
        registration.require_generation(row['registration_owner'],row['generation_id'])
        _, current = registration._state(row['registration_owner'])
        if digest(current) != row['registration_sha256']:
            raise ValueError('scoped_research_registration_changed')
        return row

    def source(self, market=None):
        row = self._record()
        if market is not None and market != row['market']:
            raise ValueError('research_source_market_not_owned')
        return deepcopy(row['source'])

    def relationship(self, market):
        row = self._record()
        source = self.source(market)
        return dict(contract=CONTRACT, market=market, generation_id=row['generation_id'],
            source_generation_id=source['source_generation_id'], subjects=list(row['subjects']),
            outer_source_envelope_sha256=row['outer_sha256'], prepared_source_sha256=row['source_sha256'],
            inner_consumed_source_sha256=digest(source), registration_sha256=row['registration_sha256'],
            subject_sha256={t:digest(dict(stock=source['stocks'][t], prepared=source['prepared'][t]))
                for t in row['subjects']})


def prepare_scoped_research_source(*, enabled=False, market, subjects, registration_owner,
                                   whole, local_seeds, valuation_contexts, generation, coverage, census,
                                   forward_views=None):
    if enabled is not True:
        raise ValueError('scoped_research_source_disabled')
    subjects = tuple(sorted(subjects))
    if market not in ('us','kr') or not subjects or len(set(subjects)) != len(subjects):
        raise ValueError('scoped_research_exact_subjects_required')
    registration.require_generation(registration_owner, generation)
    _, reg = registration._state(registration_owner)
    if (reg['market'] != market or not set(subjects) <= set(reg['bindings'])
            or set(whole['packets']) != {market}
            or set(whole['packets'][market]['stocks']) != set(subjects)
            or set(local_seeds) != set(subjects) or set(valuation_contexts) != set(subjects)):
        raise ValueError('scoped_research_registered_source_coverage')
    projector=project_production_market_context
    if whole.get('seed',{}).get('contract')=='selected-original-source-run-binding-v1':
        from app.services.selected_source_composition import project_market,SelectedSourceRunBinding
        binding=SelectedSourceRunBinding.model_validate(whole['seed'])
        if (binding.child_id!=generation or binding.market!=market or binding.subjects!=subjects
                or binding.registration_receipt_sha256!=digest(reg)):
            raise ValueError('selected_prepared_source_child_scope')
        projector=project_market
    source = prepare_monitoring_source(whole=whole, local_seeds=local_seeds,
        valuation_contexts=valuation_contexts, generation=generation, coverage=coverage, census=census,
        market_projector=projector)
    if market == 'kr':
        from app.services.kr_forward_valuation_context import KrForwardValuationView, calibration_context
        if forward_views is None or set(forward_views) != set(subjects):
            raise ValueError('scoped_research_original_kr_forward_views_required')
        source['forward_views'] = {}
        for ticker in subjects:
            view = KrForwardValuationView.model_validate(forward_views[ticker])
            if (view.native.model_dump(mode='json') != source['stocks'][ticker]['valuation_view']
                    or calibration_context(view) != valuation_contexts[ticker]):
                raise ValueError('scoped_research_kr_forward_calibration_drift')
            source['forward_views'][ticker] = view.model_dump(mode='json')
    elif forward_views:
        raise ValueError('scoped_research_unexpected_kr_forward_views')
    else:
        from app.services.provider_valuation_calibration_context import calibration_context
        if any(calibration_context(source['stocks'][t]['valuation_view']) != valuation_contexts[t] for t in subjects):
            raise ValueError('scoped_research_provider_valuation_calibration_drift')
    for ticker in subjects:
        stock, prepared = source['stocks'][ticker], source['prepared'][ticker]
        verified_owned_packet_view(stock)
        original._require(stock['ticker'] == ticker and stock['market'] == market
            and prepared['mode'] == 'EVIDENCE_BASED'
            and stock['fresh_run_id'] == source['source_generation_id']
            and prepared['initial_chain']['source_generation_id'] == source['source_generation_id']
            and prepared['initial_chain']['execution_generation_id'] == generation
            and prepared['view_receipt']['raw_source_sha256'] == digest(stock), 'original_subject_scope_required')
    handle = object.__new__(ScopedPreparedResearchOwner)
    with original._LOCK:
        original._OWNERS[handle] = dict(source=deepcopy(source), source_sha256=digest(source),
            outer_sha256=digest(whole), generation_id=generation, pid=os.getpid(), closed=False,
            market=market, subjects=subjects, registration_sha256=digest(reg), registration_owner=registration_owner)
    relation = handle.relationship(market)
    cutoffs = {_instant(source['stocks'][t]['packet']['generated_at']) for t in subjects}
    if len(cutoffs) != 1:
        handle.close()
        raise ValueError('scoped_research_inconsistent_stock_cutoffs')
    cutoff = cutoffs.pop()
    cohort = FrozenCohort(run_id=generation, source_generation=source['source_generation_id'],
        assessment_date=source['markets'][market]['packet']['assessment_date'], effective_at=cutoff, cutoff=cutoff,
        subjects=tuple(CohortSubject(market,t,reg['bindings'][t]['security_id'],cutoff,
            relation['subject_sha256'][t]) for t in subjects),
        source_owner_bindings=((market,digest(relation)),), feature_scope_sha256=digest(dict(
            purpose=CONTRACT, market=market, subjects=subjects, registration_sha256=digest(reg))), planning_only=False)
    try:
        cohort.verify_source_owner(handle)
    except Exception:
        handle.close()
        raise
    return source, handle, cohort
