from __future__ import annotations

from datetime import datetime

from app.services.krx_night_session_contract_service import (
    ChangeReferenceType,
    KrxNightFuturesSessionQuote,
    NightFuturesReferenceComparison,
    NightMarketState,
)
from app.services.leading_market_snapshot_service import (
    LeadingMarketObservation,
    LeadingMarketReferenceBasis,
    LeadingMarketRenderContext,
    LeadingMarketSessionState,
    LeadingMarketSnapshot,
    LeadingMarketSourceContract,
)


CONTRACT_VERSION = "krx-night-leading-market-adapter-v1"


def _safe_comparison(
    quote: KrxNightFuturesSessionQuote,
) -> tuple[NightFuturesReferenceComparison, LeadingMarketReferenceBasis] | None:
    basis_by_type: dict[ChangeReferenceType, LeadingMarketReferenceBasis] = {
        ChangeReferenceType.PRIOR_NIGHT_CLOSE: "PRIOR_COMPARABLE_NIGHT_CLOSE",
        ChangeReferenceType.OFFICIAL_BASE_PRICE: "PROVIDER_DOCUMENTED_REFERENCE",
        ChangeReferenceType.PROVIDER_REFERENCE: "PROVIDER_DOCUMENTED_REFERENCE",
    }
    for reference_type in (
        ChangeReferenceType.PRIOR_NIGHT_CLOSE,
        ChangeReferenceType.OFFICIAL_BASE_PRICE,
        ChangeReferenceType.PROVIDER_REFERENCE,
    ):
        for comparison in quote.comparisons:
            if (
                comparison.reference_type == reference_type
                and comparison.source_semantic_explicit
            ):
                return comparison, basis_by_type[reference_type]
    return None


def adapt_krx_night_quote_to_leading_market(
    quote: KrxNightFuturesSessionQuote,
    *,
    collected_at: datetime,
    allow_human_fixture: bool = False,
) -> LeadingMarketRenderContext:
    if quote.source_quality == "HUMAN_FIXTURE" and not allow_human_fixture:
        raise ValueError("krx_night_human_fixture_not_runtime_eligible")
    if collected_at.tzinfo is None or collected_at.utcoffset() is None:
        raise ValueError("krx_night_adapter_collection_timezone_required")

    comparison = _safe_comparison(quote)
    reference_basis = comparison[1] if comparison is not None else None
    source = LeadingMarketSourceContract(
        contract_id=CONTRACT_VERSION,
        provider=quote.source,
        market="kr",
        instrument_ids=(quote.instrument_id,),
        reference_basis=reference_basis,
        active_max_age_seconds=120,
        preopen_max_age_seconds=300,
        source_timezone="Asia/Seoul",
        official_or_existing_supported_free=True,
    )
    if quote.market_state != NightMarketState.OPEN:
        snapshot = LeadingMarketSnapshot(
            market="kr",
            session_state=LeadingMarketSessionState.STALE_FUTURES_SESSION,
            observations=(),
            collected_at=collected_at,
        )
        return LeadingMarketRenderContext(
            source_contract=source,
            snapshot=snapshot,
            validation_as_of=collected_at,
        )

    observation = LeadingMarketObservation(
        instrument_id=quote.instrument_id,
        display_name="KOSPI200 야간선물",
        provider=quote.source,
        session_id=(
            f"{quote.session_business_date.isoformat()}-XKRX-NIGHT-"
            f"{quote.contract_month}"
        ),
        current_price=float(quote.last),
        reference_price=(float(comparison[0].reference_price) if comparison else None),
        change_pct=(float(comparison[0].change_pct) if comparison else None),
        reference_basis=reference_basis,
        as_of=quote.observed_at,
        source_timezone="Asia/Seoul",
        source_document_or_endpoint=quote.source,
    )
    snapshot = LeadingMarketSnapshot(
        market="kr",
        session_state=LeadingMarketSessionState.ACTIVE_FUTURES_SESSION,
        observations=(observation,),
        collected_at=collected_at,
    )
    return LeadingMarketRenderContext(
        source_contract=source,
        snapshot=snapshot,
        validation_as_of=collected_at,
    )
