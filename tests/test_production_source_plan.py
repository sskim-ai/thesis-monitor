from copy import deepcopy
from pathlib import Path

import pytest

from app.services.production_source_plan import (
    ProductionRequestPlan, admit_request_plan, build_request_plan,
)
from app.services.sealed_fresh_dispatch import ProviderPlan, decode_request_plan
from app.services.unified_stock_event_input import make_read
from scripts.kr8_kis_integration import build_plan
from tests.test_kr8_source_scope import kr_plan
from tests.test_us14_source_scope import us_plan

ROOT = Path(__file__).resolve().parents[1]


def current_plan(market):
    args, _, _ = (us_plan if market == "us" else kr_plan)()
    args.pop("rev10_receipt")
    generation = "production-fixture-attempt-1"
    args["stock"] = args["stock"].model_copy(update={"run_id": generation})
    records = list(args["identities"].values())
    args["news_reads"] = [make_read(security=s, market=market, run_id=generation,
        lookback_days=3, security_records=records) for s in records]
    kis = None
    if market == "kr":
        kis = build_plan(generation=generation, as_of=args["stock"].frozen_at.isoformat(),
            securities={t: dict(s, currency="KRW") for t, s in args["identities"].items()},
            static_hashes={"fictional-official-protocol": "a" * 64})
    result = build_request_plan(market=market, run_id="production-fixture",
        attempt_id=generation, compiler_args=args, kis_plan=kis)
    return args, kis, result


@pytest.mark.parametrize("market", ["us", "kr"])
def test_production_plan_is_separately_versioned_and_exactly_recompiled(market):
    args, kis, result = current_plan(market)
    plan = result["plan"]
    assert isinstance(decode_request_plan(plan.model_dump(mode="json")), ProductionRequestPlan)
    assert "rev10_receipt_sha256" not in plan.model_dump()
    with pytest.raises(ValueError):
        ProviderPlan.model_validate(plan.model_dump(mode="json"))
    receipt = admit_request_plan(plan, compiler_args=args, kis_plan=kis,
        config_identities=args["config_identities"],
        credential_presence={**dict.fromkeys(args["config_identities"], True), "kis": True},
        repository_root=ROOT)
    assert receipt["status"] == "PASS", receipt
    assert not receipt["historical_receipt_dependency"]


@pytest.mark.parametrize("change", ["close", "news", "universe", "validator", "chart-close", "provider"])
def test_source_plan_rejects_unqualified_dag_before_transport(change):
    _, _, result = current_plan("us")
    raw = result["plan"].model_dump(mode="json")
    if change in {"close", "news"}:
        predicate = (lambda d: d["consumer_role"].startswith("completed_close:")) if change == "close" else (
            lambda d: d["provider"] == "google_news_rss")
        raw["descriptors"].remove(next(d for d in raw["descriptors"] if predicate(d)))
    elif change == "universe":
        raw["subjects"].append("NVDA")
    elif change == "validator":
        raw["validator_contracts"] = []
    else:
        d = next(d for d in raw["descriptors"] if d["consumer_role"].startswith("completed_close:"))
        d["endpoint_operation" if change == "chart-close" else "provider"] = (
            "usa06012" if change == "chart-close" else "alpha_vantage")
    with pytest.raises(ValueError):
        ProductionRequestPlan.model_validate(raw)


def test_kis_presence_and_generation_binding_are_pre_dispatch_gates():
    args, kis, result = current_plan("kr")
    receipt = admit_request_plan(result["plan"], compiler_args=args, kis_plan=kis,
        config_identities=args["config_identities"],
        credential_presence=dict.fromkeys(args["config_identities"], True), repository_root=ROOT)
    assert receipt["status"] == "FAIL" and "credential_presence:kis" in receipt["gaps"]
    changed = deepcopy(kis)
    changed["generation_id"] = "old"
    with pytest.raises(ValueError, match="kis_plan_changed"):
        build_request_plan(market="kr", run_id="production-fixture",
            attempt_id="production-fixture-attempt-1", compiler_args=args, kis_plan=changed)


def test_unknown_plan_version_cannot_fall_back_to_production():
    _, _, result = current_plan("us")
    raw = result["plan"].model_dump(mode="json")
    raw["contract"] = "caller-defined-plan"
    with pytest.raises(ValueError):
        decode_request_plan(raw)
