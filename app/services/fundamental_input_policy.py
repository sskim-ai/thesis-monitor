"""Source/use separation for the legacy evidence projection, not economic authority."""
from __future__ import annotations

from enum import StrEnum
import json
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, model_validator

if TYPE_CHECKING:
    from app.services.cross_market_decision_engine_service import DecisionEvidenceRef


class InputSourceClass(StrEnum):
    CANONICAL_FINANCIAL = "TYPED_CANONICAL_FINANCIAL_PROJECTION"
    CANONICAL_COMPATIBILITY = "CANONICAL_COMPATIBILITY_REQUIRES_SOURCE_ADMISSION"
    EVENT_TRIAGE = "EVENT_TRIAGE"
    USER_HYPOTHESIS = "USER_HYPOTHESIS"
    PROSPECTIVE_CONDITION = "PROSPECTIVE_CONDITION"
    PRICE_TIMING = "PRICE_TIMING"
    QUALITY_LIMIT = "QUALITY_LIMIT"
    UNADMITTED = "UNADMITTED"


class SourceUseBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract: Literal["fundamental-source-use-v1"] = "fundamental-source-use-v1"
    source_class: InputSourceClass
    producer: Literal["decision-evidence-packet-v1"] = "decision-evidence-packet-v1"
    owner_ref: str
    security_id: str
    source_ref: str
    core_current_fact: bool = False
    prospective_only: bool = False

    @model_validator(mode="after")
    def closed_permissions(self):
        if self.core_current_fact != (
            self.source_class == InputSourceClass.CANONICAL_FINANCIAL
        ):
            raise ValueError("fundamental_source_class_use_mismatch")
        if self.prospective_only != (self.source_class in {
            InputSourceClass.USER_HYPOTHESIS, InputSourceClass.PROSPECTIVE_CONDITION
        }):
            raise ValueError("fundamental_prospective_use_mismatch")
        return self


class PriceQualityLimit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract: Literal["price-quality-limit-v1"] = "price-quality-limit-v1"
    availability: Literal["ready", "price_only", "unavailable", "invalid"]
    use: Literal["EPISTEMIC_LIMIT_NOT_DIRECTIONAL_EVIDENCE"] = (
        "EPISTEMIC_LIMIT_NOT_DIRECTIONAL_EVIDENCE"
    )


def price_availability(value: object, *, contract: object = None) -> Literal["ready", "price_only", "unavailable", "invalid"]:
    # The completed-close v2 producer uses a distinct unavailable enum. This
    # conversion conveys only a nonnumeric limit, never price/source authority.
    if contract == "current-price-context-v2" and value == "UNAVAILABLE":
        return "unavailable"
    if isinstance(value, str) and value in {"ready", "price_only", "unavailable"}:
        return value
    # Existing current-price-context-v1 states convey a limit, never readiness.
    if value is None or (isinstance(value, str) and value in {"legacy_only", "partial"}):
        return "invalid"
    raise ValueError("fundamental_price_availability_invalid")


def fundamental_ref_projection(ref: DecisionEvidenceRef) -> DecisionEvidenceRef:
    """One closed view for prompt, alias and downstream fundamental evidence."""
    binding = ref.source_use
    if binding is None:
        return ref
    if binding.source_class == InputSourceClass.QUALITY_LIMIT:
        if (ref.ref_id != "quality:current_price_context"
                or ref.source_ref != "stock.current_price_context.availability"
                or binding != source_use(source_ref=ref.source_ref,
                    security_id=binding.security_id, price_quality=True)):
            raise ValueError("fundamental_quality_binding_mismatch")
        quality = PriceQualityLimit.model_validate_json(ref.statement)
        return ref.model_copy(update={
            "label": "Price data availability", "statement": quality.model_dump_json(),
            "as_of": None, "value": None, "unit": None, "metric_refs": (),
            "logical_condition": None, "source_time": None,
            "financial_context": None, "financial_value": None,
            "numeric_prose_eligible": False,
        })
    if binding.source_class == InputSourceClass.CANONICAL_FINANCIAL:
        if (not ref.source_ref.startswith("stock.fact_catalog.")
                or binding != source_use(source_ref=ref.source_ref,
                    security_id=binding.security_id, canonical=True, typed_financial=True)):
            raise ValueError("fundamental_financial_binding_mismatch")
        if ref.financial_context is None or ref.financial_value is None:
            raise ValueError("fundamental_financial_value_required")
        return ref.model_copy(update={
            "label": ref.financial_context.metric,
            "statement": json.dumps({
                "value": str(ref.financial_value),
                "context": ref.financial_context.model_dump(mode="json"),
            }, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "value": None, "unit": None, "logical_condition": None,
        })
    return ref


def source_use(*, source_ref: str, security_id: str, canonical: bool = False,
               event: bool = False, timing: bool = False,
               price_quality: bool = False,
               typed_financial: bool = False) -> SourceUseBinding:
    """Classify producer channels before category/family or display text is considered."""
    kind = InputSourceClass.UNADMITTED
    owner = "unadmitted"
    if source_ref.startswith("stock.thesis."):
        kind = (InputSourceClass.PROSPECTIVE_CONDITION
                if source_ref.rsplit(".", 1)[-1] in {
                    "strengthen_signals", "weaken_signals", "invalidation_signals"
                } else InputSourceClass.USER_HYPOTHESIS)
        owner = "stored_user_thesis"
    elif price_quality:
        kind, owner = InputSourceClass.QUALITY_LIMIT, "current_price_context_availability"
    elif source_ref == "stock.current_price_context" or timing:
        kind, owner = InputSourceClass.PRICE_TIMING, "price_timing_owner"
    elif event:
        kind, owner = InputSourceClass.EVENT_TRIAGE, "assessment_material_evidence"
    elif canonical and typed_financial:
        kind, owner = InputSourceClass.CANONICAL_FINANCIAL, "financial_context_adapter"
    elif canonical:
        kind, owner = InputSourceClass.CANONICAL_COMPATIBILITY, "canonical_fact_catalog"
    return SourceUseBinding(
        source_class=kind, owner_ref=owner, security_id=security_id,
        source_ref=source_ref,
        # Compatibility rows do not acquire permission from their category.
        core_current_fact=kind == InputSourceClass.CANONICAL_FINANCIAL,
        prospective_only=kind in {InputSourceClass.USER_HYPOTHESIS,
                                  InputSourceClass.PROSPECTIVE_CONDITION},
    )
