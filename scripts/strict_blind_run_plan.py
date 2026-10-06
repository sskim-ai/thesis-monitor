"""Exact existing cohort/model topology; source slots must be supplied pre-data."""
from scripts.r2b_r5_execution import owner
from scripts.strict_blind_controller import MARKET_CONTRACTS, MODEL_STAGES, RequestScope


def execution_plan(source_slots):
    batches = owner._batch_topology()
    subjects = [(r["market"].upper(), t) for r in batches for t in r["subjects"]]
    stages = {}
    for stage in MODEL_STAGES:
        if stage in ("BLIND", "B2"):
            rows = [dict(market=m, subjects=[t], batch=i) for i, (m, t) in enumerate(subjects, 1)]
        elif stage == "MARKET":
            rows = [dict(market=m, subjects=[], batch=1) for m in MARKET_CONTRACTS]
        else:
            rows = [dict(market=r["market"].upper(), subjects=r["subjects"], batch=r["batch"]) for r in batches]
        stages[stage] = [dict(**row, logical_id=f'{stage}:{row["market"]}:{row["batch"]}',
            scope=RequestScope.MARKET if stage == "MARKET" else RequestScope.SUBJECT,
            native_market_contract=MARKET_CONTRACTS[row["market"]] if stage == "MARKET" else None) for row in rows]
    return dict(stages=stages, source_slots=list(source_slots), model="gpt-5.6-sol", effort="xhigh",
        timeout_seconds=600, retries=2, caps={s: 30 if s in ("BLIND", "B2") else len(stages[s]) * 3
            for s in MODEL_STAGES})
