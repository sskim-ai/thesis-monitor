"""Explicit market-only acquisition; never a full stock/source qualification."""

from app.services.unified_snapshot_contract import digest

CONTRACT = "canonical-market-delta-v1"
PHASES = ("us-market", "kr-market")


def market_only_plan(plan):
    """Restrict an already compiled plan, preserving each original descriptor."""

    def allowed(name):
        return name == "kiwoom:auth" or name.startswith(("us_market:", "kr_market:"))

    data = plan.model_dump(mode="json")
    data["descriptors"] = [d for d in data["descriptors"] if allowed(d["logical_request_id"])]
    data["mandatory_roles"] = [
        r
        for r in data["mandatory_roles"]
        if r == "kiwoom:credential_exchange" or r.startswith(("us_market:", "kr_market:"))
    ]
    data["unresolved_roles"] = [
        r for r in data.get("unresolved_roles", []) if r.startswith(("us_market:", "kr_market:"))
    ]
    result = type(plan).model_validate(data)
    scope = dict(
        contract=CONTRACT,
        phases=list(PHASES),
        full_compiled_plan_sha256=plan.plan_sha256,
        restricted_plan_sha256=result.plan_sha256,
        descriptors_sha256=digest(data["descriptors"]),
        stock_acquisition="NOT_RUN",
        model_execution="NOT_AUTHORIZED_BY_ACQUISITION",
    )
    return result, scope


def require_market_delta(frozen, plan):
    scope = frozen.get("market_delta")
    if scope is None:
        return None
    if (
        scope.get("contract") != CONTRACT
        or scope.get("phases") != list(PHASES)
        or scope.get("restricted_plan_sha256") != plan.plan_sha256
        or scope.get("descriptors_sha256")
        != digest([d.model_dump(mode="json") for d in plan.descriptors])
        or frozen.get("generation_id") != plan.generation_id
        or frozen.get("scope") in {"KR8_ONLY", "US14_ONLY"}
    ):
        raise ValueError("market_delta_scope_binding")
    ids = {d.logical_request_id for d in plan.descriptors}
    if (
        "kiwoom:auth" not in ids
        or not any(i.startswith("us_market:") for i in ids)
        or not any(i.startswith("kr_market:") for i in ids)
        or any(i != "kiwoom:auth" and not i.startswith(("us_market:", "kr_market:")) for i in ids)
        or any(d.provider != "kiwoom" for d in plan.descriptors)
    ):
        raise ValueError("market_delta_nonmarket_descriptor")
    return frozenset(PHASES)
