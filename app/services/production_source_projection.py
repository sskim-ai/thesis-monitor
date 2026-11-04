"""Current production sources are re-owned from raw receipts before Monitoring."""
from pathlib import Path

from app.services.canonical_monitoring_source import prepare_monitoring_source
from app.services.canonical_source_composition import compose_source_owners
from app.services.canonical_source_inputs import build_source_replay_inputs
from app.services.canonical_source_replay import read
from app.services.current_source_coverage import SourceOwners, SEMANTICS, seal_inputs, compose
from app.services.production_source_binding import ProductionSourceRunBinding
from app.services.production_source_plan import ProductionRequestPlan
from app.services.provider_valuation_calibration_context import calibration_context
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE


def replay_source_owners(root, frozen, outcome, policy, *, runtime_policy_sha256):
    root = Path(root)
    plan = ProductionRequestPlan.model_validate(frozen["plan"])
    if (frozen["generation_id"] != plan.attempt_id or frozen["frozen_at"] != plan.frozen_at.isoformat()
            or frozen["scope"] != ("US14_ONLY" if plan.market == "us" else "KR8_ONLY")):
        raise ValueError("production_source_frozen_plan_identity")

    def binding_factory(**values):
        return ProductionSourceRunBinding(market=plan.market, run_id=plan.run_id,
            attempt_id=plan.attempt_id, request_plan_sha256=plan.plan_sha256,
            runtime_source_policy_sha256=runtime_policy_sha256, **values)

    args = build_source_replay_inputs(root, frozen, outcome, policy,
        binding_factory=binding_factory)
    first, second = compose_source_owners(**args), compose_source_owners(**args)
    if first != second or set(first["packets"]) != {plan.market}:
        raise ValueError("production_canonical_source_replay_drift")
    return args, first


def coverage_from_owned_sources(root, frozen, whole, *, collection_seal_sha256,
                               kis_plan=None, kis_view=None, kis_root=None):
    """Collection seals bind bytes; unchanged typed owners determine eligibility."""
    from app.services.bounded_financial_projection import project
    root = Path(root)
    plan = ProductionRequestPlan.model_validate(frozen["plan"])
    stocks = whole["packets"][plan.market]["stocks"]
    if set(stocks) != set(UNIVERSE[plan.market]):
        raise ValueError("production_source_exact_cohort_required")
    securities = {r["ticker"]: r for r in frozen["security_records"]}
    owners = {}
    if plan.market == "kr" and (kis_plan is None or kis_view is None or kis_root is None
                                or digest(kis_plan) != plan.kis_plan_sha256):
        raise ValueError("production_kis_source_binding_required")
    for ticker, stock in stocks.items():
        args = {}
        fact = stock["quality_view"]["fact"]
        if fact is not None and fact["issuer_business_bridge"]:
            underlying = fact["source_ticker"]
            directory = root / "financial" / underlying
            args["business_projection"] = project(frozen["candidate"]["financial_plans"][underlying],
                read(directory / "owner-acquisition.json"), directory,
                read(directory / "owner-receipts.json"), field_semantics=True)
        if plan.market == "kr":
            row = next(r for r in kis_view["rows"] if r["security_code"] == ticker)
            directory = Path(kis_root) / "estimate"
            evidence = dict(code=ticker, generation=kis_plan["generation_id"], plan=kis_plan,
                raw=(directory / (ticker + ".body")).read_bytes(),
                receipt=read(directory / (ticker + "-receipt.json")),
                request=read(directory / (ticker + "-request.json")))
            args.update(kis_row=row, kis_plan=kis_plan, kis_corpus_sha256=digest(kis_view),
                        availability_inputs=evidence)
        owners[ticker] = SourceOwners(generation=plan.generation_id, stock=stock,
            security=securities[ticker], collection_receipt_sha256=collection_seal_sha256, **args)
    subjects = sorted(owners)
    inputs = seal_inputs(owners, subjects=subjects, semantics_version=SEMANTICS)
    result = compose(owners, subjects=subjects, generations={t: o.generation for t, o in owners.items()},
        input_seal=inputs, input_seal_sha256=inputs["receipt_sha256"], semantics_version=SEMANTICS)
    if (result["coverage"]["complete_subjects"] != len(subjects)
            or result["coverage"]["unresolved_required_cells"] != 0 or result["census"] is None
            or any(r["evaluability"]["evaluability_state"] == "INVALID_INCOMPLETE_CONTRACT"
                   for r in result["resolutions"].values())):
        raise ValueError("production_current_source_owner_coverage_gap")
    return result


def monitoring_source(*, args, whole, frozen, coverage, kis_plan=None, kis_view=None):
    plan = ProductionRequestPlan.model_validate(frozen["plan"])
    forward_views = {}
    local = {t: i["fresh_financial_binding"]["technical_inputs"]["local_seed"]
             for t, i in args["stock_inputs"].items()}
    if plan.market == "kr":
        from app.services.kr_current_valuation_projection import source_only_projection
        from app.services.kr_forward_valuation_context import KrForwardValuationView
        from app.services.kr_forward_valuation_context import calibration_context as kr_context
        projection = source_only_projection(whole, source_view=kis_view,
            provider_plan=frozen, kis_plan=kis_plan)
        valuations = projection["expected_valuation_contexts"]
        for ticker, stock in whole["packets"]["kr"]["stocks"].items():
            view = KrForwardValuationView(native=stock["valuation_view"],
                **projection["stocks"][ticker]["kr_fy1_evidence"])
            if kr_context(view) != valuations[ticker]:
                raise ValueError("production_kr_valuation_projection_drift")
            forward_views[ticker] = view.model_dump(mode="json")
    else:
        valuations = {t: calibration_context(s["valuation_view"])
                      for t, s in whole["packets"][plan.market]["stocks"].items()}
    result = prepare_monitoring_source(whole=whole, local_seeds=local, valuation_contexts=valuations,
        generation=plan.generation_id, coverage=coverage["coverage"], census=coverage["census"])
    if plan.market == "kr":
        result["forward_views"] = forward_views
    return result
