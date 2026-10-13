"""Versioned production execution lineage, never a proof seed authorization."""
from typing import Literal

from pydantic import Field, model_validator

from app.services.canonical_source_composition import SourceRunBinding
from app.services.unified_stock_acquisition import UNIVERSE

SHA = r"^[a-f0-9]{64}$"


class ProductionSourceRunBinding(SourceRunBinding):
    contract: Literal["production-source-run-binding-v1"] = "production-source-run-binding-v1"
    execution_purpose: Literal["PRODUCTION_MONITORING"] = "PRODUCTION_MONITORING"
    market: Literal["us", "kr"]
    run_id: str
    attempt_id: str
    request_plan_sha256: str = Field(pattern=SHA)
    runtime_source_policy_sha256: str = Field(pattern=SHA)
    fresh_stock_owner_set_sha256: str = Field(pattern=SHA)
    auxiliary_issuer_set_sha256: str | None = Field(default=None, pattern=SHA)

    @property
    def universe(self):
        return {self.market: UNIVERSE[self.market]}

    @property
    def fresh_mode(self):
        return True

    @property
    def us_only(self):
        return self.market == "us"

    @property
    def kr_only(self):
        return self.market == "kr"

    @property
    def cohort_metadata(self):
        return dict(contract="production-source-cohort-v1", execution_purpose="PRODUCTION_MONITORING")

    @model_validator(mode="after")
    def current_execution_identity(self):
        if (self.parent_run_id != self.attempt_id or
                not self.attempt_id.startswith(self.run_id + "-attempt-")):
            raise ValueError("production_generation_binding_required")
        if self.us_only != (self.auxiliary_issuer_set_sha256 is not None):
            raise ValueError("production_auxiliary_scope_mismatch")
        return self
