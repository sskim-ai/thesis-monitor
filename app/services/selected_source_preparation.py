"""Original Coverage/FY1 -> selected canonical Owner -> existing NO-SEND child."""
from pathlib import Path

from app.services.unified_snapshot_contract import digest


def coverage_and_forward(*,root,frozen,whole,collection_seal_sha256,kis_plan=None,kis_view=None,business_projections=None):
    from app.services.selected_source_plan import SelectedRequestPlan
    from app.services.selected_source_composition import SelectedSourceRunBinding
    from app.services.canonical_source_replay import read
    from app.services.current_source_coverage import SourceOwners,SEMANTICS,seal_inputs,compose
    from app.services.kr_forward_valuation_context import KrForwardValuationView,calibration_context
    from app.services.provider_valuation_calibration_context import calibration_context as us_context
    plan=SelectedRequestPlan.model_validate(frozen['plan'])
    binding=SelectedSourceRunBinding.model_validate(whole['seed'])
    stocks=whole['packets'][plan.market]['stocks']
    if (set(stocks)!=set(plan.subjects) or binding.child_id!=plan.generation_id
            or binding.market!=plan.market or binding.subjects!=plan.subjects
            or binding.request_plan_sha256!=plan.plan_sha256):
        raise ValueError('selected_coverage_child_or_subjects')
    securities={s['ticker']:s for s in frozen['security_records']}
    if set(securities)!=set(plan.subjects):raise ValueError('selected_coverage_security_scope')
    if plan.market=='kr':
        from app.services.selected_kis_sources import validate_plan
        if (kis_plan is None or validate_plan(kis_plan)!=plan.subjects or digest(kis_plan)!=plan.kis_plan_sha256
                or kis_view is None or kis_view['generation_id']!=plan.generation_id
                or kis_view['rows_sha256']!=digest(kis_view['rows'])
                or len(kis_view['rows'])!=len(plan.subjects)
                or {r['security_code'] for r in kis_view['rows']}!=set(plan.subjects)):
            raise ValueError('selected_kis_original_source_binding')
    elif kis_plan is not None or kis_view is not None:raise ValueError('selected_us_kis_scope')
    owners,forward,contexts={},{},{}
    for ticker,stock in stocks.items():
        extra={}
        if stock.get('issuer_business_bridge'):
            # A non-direct issuer projection must be supplied by its original
            # bound source; no guessed underlying relationship is introduced.
            if ticker not in (business_projections or {}):
                raise ValueError('selected_bridge_original_projection_required')
            extra['business_projection']=business_projections[ticker]
        if plan.market=='kr':
            row=next(r for r in kis_view['rows'] if r['security_code']==ticker)
            view=KrForwardValuationView(native=stock['valuation_view'],kis=row,as_of=kis_plan['as_of'],
                fresh_plan_sha256=kis_plan['receipt_sha256'],source_corpus_sha256=digest(kis_view))
            forward[ticker]=view.model_dump(mode='json');contexts[ticker]=calibration_context(view)
            folder=Path(root)/'kis/estimate'
            evidence=dict(code=ticker,generation=plan.generation_id,plan=kis_plan,
                raw=(folder/(ticker+'.body')).read_bytes(),receipt=read(folder/(ticker+'-receipt.json')),
                request=read(folder/(ticker+'-request.json')))
            extra.update(kis_row=row,kis_plan=kis_plan,kis_corpus_sha256=digest(kis_view),availability_inputs=evidence)
        else:contexts[ticker]=us_context(stock['valuation_view'])
        owners[ticker]=SourceOwners(generation=plan.generation_id,stock=stock,security=securities[ticker],
            collection_receipt_sha256=collection_seal_sha256,**extra)
    seal=seal_inputs(owners,subjects=list(plan.subjects),semantics_version=SEMANTICS)
    result=compose(owners,subjects=list(plan.subjects),generations={t:plan.generation_id for t in plan.subjects},
        input_seal=seal,input_seal_sha256=seal['receipt_sha256'],semantics_version=SEMANTICS)
    if not result['coverage']['coverage_complete'] or result['census'] is None:
        raise ValueError('selected_original_coverage_required_cells_incomplete')
    if result['contexts']!=contexts:raise ValueError('selected_forward_coverage_context_drift')
    return result,forward


def prepare_child(*,root,frozen,outcome,policy,registration_owner,kis_plan=None,enabled=False):
    if enabled is not True:raise ValueError('selected_source_preparation_default_off')
    from app.services.selected_source_composition import SelectedSourceRunBinding
    from app.services.canonical_source_inputs import build_source_replay_inputs
    from app.services.canonical_source_composition import compose_source_owners
    from app.services.scoped_monitoring_research import prepare_scoped_research_source
    from app.services.model_execution_plan import compile_model_plan
    from app.services.research_no_send_run import MarketResearchChild
    market=frozen['selected_market']
    args=build_source_replay_inputs(Path(root),frozen,outcome,policy,binding_factory=SelectedSourceRunBinding,
        prospective_owners={market:registration_owner})
    whole=compose_source_owners(**args)
    kis=None
    if market=='kr':
        from app.services.production_kis_sources import replay_current_kis
        kis=replay_current_kis(Path(root),frozen,outcome,kis_plan)
    projections={}
    for ticker,item in args['stock_inputs'].items():
        fin=item['fresh_financial_binding']['financial_inputs']
        if fin.get('issuer_business'):
            from app.services.bounded_financial_stock_owner import replay_issuer_source
            owned=replay_issuer_source(fin['issuer_business']['source_inputs'],target_plan=fin['plan'])
            if owned['status']!='PASS':raise ValueError('selected_original_issuer_projection_denied')
            projections[ticker]=owned['projection']
    coverage,forward=coverage_and_forward(root=root,frozen=frozen,whole=whole,
        collection_seal_sha256=digest(outcome),kis_plan=kis_plan,kis_view=kis,business_projections=projections)
    local={t:v['fresh_financial_binding']['technical_inputs']['local_seed'] for t,v in args['stock_inputs'].items()}
    source,owner,cohort=prepare_scoped_research_source(enabled=True,market=market,subjects=tuple(local),
        registration_owner=registration_owner,whole=whole,local_seeds=local,
        valuation_contexts=coverage['contexts'],generation=frozen['generation_id'],
        coverage=coverage['coverage'],census=coverage['census'],forward_views=forward or None)
    try:
        child=MarketResearchChild(compile_model_plan(cohort,topology='CANONICAL_PRODUCTION'),owner)
        child.verify()
    except Exception:
        owner.close();raise
    return child,dict(whole=whole,source=source,coverage=coverage,forward_views=forward,
        model_invocations=0,delivery_invocations=0)
