from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

from app.config import get_settings
from app.services.kr_price_structure_selective_rollout_service import (
    KrPriceStructureEligibility,
    build_price_structure_runtime_context,
    classify_kr_price_structure,
    summary_for_price_structure_render,
)
from app.services.price_structure_v3_renderer_service import (
    PriceStructureRender,
    render_current_price_structure,
    validate_price_structure_render,
)


CONTRACT_VERSION = "us-price-structure-selective-rollout-v1"
RUNTIME_CONTEXT_VERSION = "us-price-structure-runtime-context-v1"


@dataclass(frozen=True)
class UsPriceStructureRolloutDecision:
    contract: str
    ticker: str
    market: str
    enabled: bool
    monitored_subject: bool
    eligibility: KrPriceStructureEligibility
    section: str | None
    numeric_bindings: tuple[dict[str, object], ...]
    displayed_zone_ids: tuple[str, ...]
    denial_reasons: tuple[str, ...]
    render_validation_errors: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_us_price_structure_rollout_decision(
    context: Mapping[str, object],
    *,
    ticker: str,
    monitored_subject: bool,
    enabled: bool | None = None,
) -> UsPriceStructureRolloutDecision:
    market = str(context.get("market") or ("KR" if ticker.isdigit() else "US"))
    effective_enabled = (
        get_settings().us_price_structure_v3_enabled
        if enabled is None
        else enabled
    )
    reasons: list[str] = []
    if market != "US" or ticker.isdigit():
        reasons.append("us_market_scope_required")
    if not monitored_subject:
        reasons.append("subject_outside_monitored_us_universe")
    eligibility = classify_kr_price_structure(context)
    if eligibility == KrPriceStructureEligibility.BLOCKED:
        reasons.append("price_structure_validation_blocked")
    elif eligibility == KrPriceStructureEligibility.OMIT_PRICE_STRUCTURE:
        reasons.append("no_safe_current_sr")
    if not effective_enabled:
        reasons.append("us_price_structure_rollout_disabled")
    if reasons:
        return UsPriceStructureRolloutDecision(
            contract=CONTRACT_VERSION,
            ticker=ticker,
            market=market,
            enabled=effective_enabled,
            monitored_subject=monitored_subject,
            eligibility=eligibility,
            section=None,
            numeric_bindings=(),
            displayed_zone_ids=(),
            denial_reasons=tuple(reasons),
            render_validation_errors=(),
        )

    render: PriceStructureRender = render_current_price_structure(
        summary_for_price_structure_render(context, eligibility),
        ticker=ticker,
        as_of=str(context.get("as_of") or ""),
        current_price=context.get("current_price"),
        currency=str(context.get("currency") or "USD"),
        include_current_price=True,
        enforce_user_visible_proximity=True,
    )
    validation = validate_price_structure_render(render)
    if validation.status == "FAIL":
        return UsPriceStructureRolloutDecision(
            contract=CONTRACT_VERSION,
            ticker=ticker,
            market=market,
            enabled=effective_enabled,
            monitored_subject=monitored_subject,
            eligibility=KrPriceStructureEligibility.BLOCKED,
            section=None,
            numeric_bindings=(),
            displayed_zone_ids=(),
            denial_reasons=("price_structure_render_validation_failed",),
            render_validation_errors=validation.errors,
        )
    return UsPriceStructureRolloutDecision(
        contract=CONTRACT_VERSION,
        ticker=ticker,
        market=market,
        enabled=effective_enabled,
        monitored_subject=monitored_subject,
        eligibility=eligibility,
        section=render.section,
        numeric_bindings=render.numeric_bindings,
        displayed_zone_ids=render.displayed_zone_ids,
        denial_reasons=(),
        render_validation_errors=(),
    )


def build_us_price_structure_runtime_context(
    *,
    ticker: str,
    cutoff: str,
    raw_by_timeframe: Mapping[str, Sequence[Mapping[str, object]]],
    observed_at: str,
    provider_limit: int,
) -> dict[str, object]:
    return build_price_structure_runtime_context(
        ticker=ticker,
        security_id=f"US_LISTED:{ticker}",
        market="US",
        currency="USD",
        runtime_contract=RUNTIME_CONTEXT_VERSION,
        cutoff=cutoff,
        raw_by_timeframe=raw_by_timeframe,
        observed_at=observed_at,
        provider_limit=provider_limit,
    )
