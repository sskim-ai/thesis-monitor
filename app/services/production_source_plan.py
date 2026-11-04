"""Current-cycle source dispatch authorization, separate from historical proof."""
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from app.services.canonical_source_plan import compile_slots
from app.services.sealed_fresh_dispatch import RequestPlan
from app.services.sealed_response_binding import binding_owner_hash
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE

CONTRACT = "production-source-request-plan-v1"
VALIDATORS = ("canonical-finite-source-slots-v1", "same-generation-owner-replay-v1")
SHA = r"^[a-f0-9]{64}$"


class ProductionRequestPlan(RequestPlan):
    contract: Literal["production-source-request-plan-v1"] = CONTRACT
    purpose: Literal["PRODUCTION_MONITORING"] = "PRODUCTION_MONITORING"
    market: Literal["us", "kr"]
    subjects: tuple[str, ...]
    run_id: str
    attempt_id: str
    stock_plan_sha256: str = Field(pattern=SHA)
    compiler_input_sha256: str = Field(pattern=SHA)
    compiler_output_sha256: str = Field(pattern=SHA)
    validator_contracts: tuple[str, ...] = VALIDATORS
    kis_plan_sha256: str | None = Field(default=None, pattern=SHA)
    alpha_vantage_planned_calls: Literal[0] = 0
    undeclared_fallbacks: tuple[()] = ()

    @model_validator(mode="after")
    def production_binding(self):
        if (self.subjects != UNIVERSE[self.market] or self.generation_id != self.attempt_id
                or not self.attempt_id.startswith(self.run_id + "-attempt-")):
            raise ValueError("production_source_plan_generation_universe")
        if self.validator_contracts != VALIDATORS:
            raise ValueError("production_source_plan_validator_missing")
        if self.market == "kr" and self.kis_plan_sha256 is None:
            raise ValueError("production_kis_plan_binding_missing")
        if self.market == "us" and self.kis_plan_sha256 is not None:
            raise ValueError("production_us_kis_scope_denied")
        close = [d for d in self.descriptors if d.consumer_role.startswith("completed_close:")]
        if self.market == "us":
            if (sorted(d.subject for d in close) != sorted(self.subjects)
                    or any(d.provider != "kiwoom" or d.endpoint_operation != "usa20590"
                           or not d.mandatory for d in close)):
                raise ValueError("PLAN_GAP_usa20590_14_of_14")
        elif close:
            raise ValueError("production_kr_us_close_scope")
        news_provider = "google_news_rss" if self.market == "us" else "naver_news"
        news = [d for d in self.descriptors if d.provider == news_provider]
        if sorted(d.subject for d in news) != sorted(self.subjects):
            raise ValueError("PLAN_GAP_event_source_coverage")
        if any(d.endpoint_operation.startswith("usa060") and d.consumer_role.startswith("completed_close:")
               for d in self.descriptors):
            raise ValueError("usa06012_completed_close_denied")
        return self


def _compiler_identity(args):
    return digest({k: (v.model_dump(mode="json") if hasattr(v, "model_dump") else
        [r.model_dump(mode="json") for r in v] if k == "news_reads" else v)
        for k, v in args.items()})


def build_request_plan(*, market, run_id, attempt_id, compiler_args, kis_plan=None):
    """Recompile the fixed DAG; a caller cannot supply an admitted slot list."""
    stock = compiler_args["stock"]
    if (stock.universe != {market: UNIVERSE[market]} or stock.run_id != attempt_id):
        raise ValueError("production_stock_plan_scope")
    if kis_plan is not None:
        from scripts.kr8_kis_integration import build_plan
        expected = build_plan(generation=attempt_id, as_of=stock.frozen_at.isoformat(),
            securities=kis_plan["securities"], static_hashes=kis_plan["static_hashes"])
        if kis_plan != expected:
            raise ValueError("production_kis_plan_changed")
    result = compile_slots(**compiler_args)
    plan = result["plan"]
    composition = {k: v for k, v in result.items() if k != "plan"}
    current = ProductionRequestPlan(**plan.model_dump(), market=market,
        subjects=UNIVERSE[market], run_id=run_id, attempt_id=attempt_id,
        stock_plan_sha256=digest(stock.model_dump(mode="json")),
        compiler_input_sha256=_compiler_identity(compiler_args),
        compiler_output_sha256=digest(composition),
        kis_plan_sha256=digest(kis_plan) if kis_plan is not None else None)
    return {**result, "plan": current}


def admit_request_plan(plan, *, compiler_args, kis_plan, config_identities,
                       credential_presence, repository_root):
    """Only current code/config and canonical re-compilation grant dispatch."""
    plan = ProductionRequestPlan.model_validate(plan)
    rebuilt = build_request_plan(market=plan.market, run_id=plan.run_id,
        attempt_id=plan.attempt_id, compiler_args=compiler_args, kis_plan=kis_plan)
    issues = []
    if rebuilt["plan"] != plan:
        issues.append("canonical_plan_replay_mismatch")
    if plan.binding_owner_sha256 != binding_owner_hash():
        issues.append("response_binding_owner_drift")
    if plan.unresolved_roles:
        issues.extend(plan.unresolved_roles)
    root = Path(repository_root).resolve()
    for name, expected in rebuilt["owners"].items():
        target = root / name
        if (target.is_symlink() or not target.resolve().is_relative_to(root)
                or not target.is_file() or sha256_bytes(target.read_bytes()) != expected):
            issues.append("normalizer_owner_drift:" + name)
    covered = {d.consumer_role for d in plan.descriptors if d.mandatory}
    issues.extend("PLAN_GAP:" + r for r in plan.mandatory_roles if r not in covered)
    for descriptor in plan.descriptors:
        if config_identities.get(descriptor.provider) != descriptor.config_identity_sha256:
            issues.append("config_binding:" + descriptor.provider)
        if credential_presence.get(descriptor.provider) is not True:
            issues.append("credential_presence:" + descriptor.provider)
    if plan.market == "kr" and credential_presence.get("kis") is not True:
        issues.append("credential_presence:kis")
    return dict(contract="production-source-admission-v1",
        status="FAIL" if issues else "PASS", live_dispatch_allowed=not issues,
        generation_id=plan.generation_id, plan_sha256=plan.plan_sha256,
        gaps=sorted(set(issues)), historical_receipt_dependency=False)
