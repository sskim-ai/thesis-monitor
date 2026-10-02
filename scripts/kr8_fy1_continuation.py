"""Source-only continuation plumbing. No acquisition or new model semantics."""
from copy import deepcopy

from app.services.current_fresh_valuation import CurrentValuationView
from app.services.kr_forward_valuation_context import (
    KrForwardValuationView, calibration_context, forward_states,
)
from app.services.unified_snapshot_contract import digest
from scripts.fresh_source_only_export import (
    source_only_generation_preflight, source_only_fresh_stock,
    source_only_market, reject_review_contamination,
)
from scripts.kr8_source_scope import require_kr8_plan
from scripts.kr8_kis_integration import SUBJECTS
from scripts.kr8_fy1_models import Kr8Execution


class Kr8Continuation(Kr8Execution):
    SUCCESS_TERMINAL = 'R2B_R9_REV40_R2_KR8_FROZEN_SOURCE_8_MESSAGE_PASS_READY_FOR_BLIND_REVIEW'


def source_only_projection(whole, *, source_view, provider_plan, kis_plan):
    identity = source_only_generation_preflight(whole,
        source_view_generation_id=source_view.get('generation_id'),
        provider_generation_id=provider_plan.get('generation_id'),
        kis_generation_id=kis_plan.get('generation_id'))
    require_kr8_plan(provider_plan)
    expected = set(SUBJECTS)
    if (set(whole['packets']) != {'kr'} or
            set(whole['packets']['kr']['stocks']) != expected or
            set(whole['authority_graph']['stocks']) != expected or
            source_view.get('scope') != 'KR8_ONLY' or len(source_view['rows']) != len(expected) or
            {r['security_code'] for r in source_view['rows']} != expected or
            source_view['rows_sha256'] != digest(source_view['rows'])):
        raise ValueError('source_only_kr8_frozen_roster_or_hash_mismatch')
    stocks, contexts, matrix = {}, {}, []
    for ticker in SUBJECTS:
        source = whole['packets']['kr']['stocks'][ticker]
        if source['fresh_run_id'] != identity['generation_id']:
            raise ValueError('source_only_stock_generation_mismatch')
        bound = KrForwardValuationView(
            native=CurrentValuationView.model_validate(source['valuation_view']),
            kis=next(r for r in source_view['rows'] if r['security_code'] == ticker),
            as_of=kis_plan['as_of'], fresh_plan_sha256=kis_plan['receipt_sha256'],
            source_corpus_sha256=digest(source_view))
        if bound.kis['eps']['state'] not in {
                'KIS_FY1_EPS_ESTIMATE_SNAPSHOT', 'UNAVAILABLE_NO_KIS_RESEARCH_ESTIMATE'}:
            raise ValueError('source_only_kis_eps_not_qualified:' + ticker)
        if bound.kis['provider_per']['state'] not in {
                'KIS_PROVIDER_FY1_PER_SNAPSHOT', 'UNAVAILABLE_NO_KIS_RESEARCH_ESTIMATE',
                'UNAVAILABLE_NO_PER_ROW'}:
            raise ValueError('source_only_kis_research_per_not_qualified:' + ticker)
        row = source_only_fresh_stock(source, whole['authority_graph']['stocks'][ticker])
        # Native valuation is already projected above; do not re-export unselected inventories.
        row['kr_fy1_evidence'] = bound.model_dump(mode='json', exclude={'native'})
        reject_review_contamination(row)
        stocks[ticker] = row
        contexts[ticker] = calibration_context(bound)
        matrix.append(dict(ticker=ticker, current_native=deepcopy(source['valuation_view']['metrics']),
            forward=forward_states(bound), current_fper=deepcopy(bound.kis['current_fper'])))
    market = source_only_market(whole['packets']['kr'], generation_id=identity['generation_id'])
    return dict(identity=identity, stocks=stocks, markets={'kr': market}, matrix=matrix,
                expected_valuation_contexts=contexts,
                source_hashes=dict(whole=digest(whole), kis=digest(source_view),
                                   provider=digest(provider_plan), kis_plan=digest(kis_plan)))
