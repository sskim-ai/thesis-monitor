"""KIS consumes the current receipt-bound DART inventory, never a saved result."""
from urllib.parse import urlsplit

from app.services.production_source_plan import ProductionRequestPlan
from app.services.production_source_seal import read
from app.services.sealed_fresh_dispatch import consume_bound_result
from scripts import kr8_kis_integration as kis


def _source_plan(frozen):
    if frozen.get('scope') == 'SELECTED_ORIGINAL_RESEARCH_V1':
        from app.services.selected_source_plan import SelectedRequestPlan
        return SelectedRequestPlan.model_validate(frozen['plan'])
    return ProductionRequestPlan.model_validate(frozen['plan'])


def current_inventories(root, frozen, outcome):
    plan = _source_plan(frozen)
    if plan.market != "kr":
        raise ValueError("production_kis_market_scope")
    result = {}
    for code in plan.subjects:
        path = root / "financial" / code
        candidates = [r for r in read(path / "owner-receipts.json") if r["stage"] == "discovery" and not r["failure_class"]]
        if len(candidates) != 1:
            raise ValueError("KIS_COMPLETE_SINGLE_INVENTORY_REQUIRED")
        row = candidates[0]
        original = read(path / (row["artifact"].split("-attempt-")[0] + ".plan.json"))
        final = outcome["logical_results"][row["sealed_logical_id"]]
        if (row["sealed_generation_id"] != frozen["generation_id"]
                or final["receipt_sha256"] != row["sealed_final_receipt_sha256"]
                or kis.digest(original) != row["request_sha256"]):
            raise ValueError("production_kis_inventory_binding")
        consume_bound_result(root=root / "dispatch", plan=plan, logical_id=row["sealed_logical_id"],
                             receipt_sha256=final["receipt_sha256"])
        receipt = dict(http_status=row["HTTP_status"], raw_sha256=row["raw_sha256"],
            request=dict(path=urlsplit(original["url"]).path, params=original["params"]),
            generation_id=frozen["generation_id"], sealed_final_receipt_sha256=final["receipt_sha256"])
        result[code] = kis.normalized_inventory(kis.evidence(path / row["artifact"]), receipt,
            code=code, corp_code=frozen["candidate"]["financial_plans"][code]["issuer"])
    return result


def replay_current_kis(root, frozen, outcome, plan):
    if kis.digest(plan) != _source_plan(frozen).kis_plan_sha256:
        raise ValueError("production_kis_plan_binding")
    args = kis.semantic_inputs(root / "static/kis", plan["static_hashes"])
    inventories = current_inventories(root, frozen, outcome)
    first = kis.replay(root / "kis", plan, inventories=inventories, **args)
    second = kis.replay(root / "kis", plan, inventories=inventories, **args)
    if first != second:
        raise ValueError("production_kis_owner_replay_drift")
    return first
