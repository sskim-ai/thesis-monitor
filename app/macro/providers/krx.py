from datetime import datetime, time
from zoneinfo import ZoneInfo

from app.jobs.probe_krx_night_futures import fetch_live_probe
from app.macro.providers.base import (
    CollectedObservation,
    MacroProviderResult,
)


KST = ZoneInfo("Asia/Seoul")
SERIES_CODES = {
    "KOSPI200": "KRX_KOSPI200_NIGHT_FUT",
    "KOSDAQ150": "KRX_KOSDAQ150_NIGHT_FUT",
}


class KrxNightFuturesProvider:
    name = "krx_night_futures"

    async def collect(self, as_of: datetime) -> MacroProviderResult:
        run_date = as_of.astimezone(KST).date()
        probe = await fetch_live_probe(run_date=run_date)
        if not probe.night_session_usable:
            return MacroProviderResult(
                provider=self.name,
                warnings=[probe.reason or "night_session_unavailable"],
            )
        observations: list[CollectedObservation] = []
        for item in probe.observations:
            observed_at = datetime.combine(item.session_date, time(6), tzinfo=KST)
            observations.append(
                CollectedObservation(
                    series_code=SERIES_CODES[item.product],
                    category="kr_night_futures",
                    observed_at=observed_at,
                    value=item.night_close,
                    unit="index_points",
                    frequency="daily",
                    market_session="kr_night",
                    previous_value=item.regular_close,
                    change_value=item.point_change,
                    change_pct=item.change_pct,
                    source_url=probe.source_url,
                    quality_status=probe.session_freshness,
                    raw_payload={
                        "product": item.product,
                        "instrument": item.product,
                        "contract_code": item.contract_code,
                        "contract_name": item.contract_name,
                        "expiry": item.maturity,
                        "exchange": item.exchange,
                        "session_basis_contract": (
                            "night-futures-session-basis-v1"
                        ),
                        "session_type": item.session_type,
                        "session_date": item.session_date.isoformat(),
                        "trade_date": item.session_date.isoformat(),
                        "session_open": datetime.combine(
                            item.reference_date, time(18), tzinfo=KST
                        ).isoformat(),
                        "session_close": observed_at.isoformat(),
                        "reference_session": item.reference_session,
                        "reference_date": item.reference_date.isoformat(),
                        "reference_price": item.reference_price,
                        "current_session_price": item.current_session_price,
                        "comparison_semantic": item.comparison_semantic,
                        "expected_latest_session_date": (
                            probe.expected_latest_session_date.isoformat()
                            if probe.expected_latest_session_date
                            else None
                        ),
                        "session_freshness": probe.session_freshness,
                        "queried_dates": [value.isoformat() for value in probe.queried_dates],
                        "date_statuses": [
                            value.model_dump(mode="json") for value in probe.date_statuses
                        ],
                        "night_close": item.night_close,
                        "regular_close": item.regular_close,
                        "point_change": item.point_change,
                        "change_pct": item.change_pct,
                        "night_source_record_id": item.night_source_record_id,
                        "reference_source_record_id": item.reference_source_record_id,
                        "night_source_payload_sha256": (
                            item.night_source_payload_sha256
                        ),
                        "reference_source_payload_sha256": (
                            item.reference_source_payload_sha256
                        ),
                        "session_evidence": item.session_evidence,
                    },
                )
            )
        return MacroProviderResult(
            provider=self.name,
            observations=observations,
            warnings=(probe.warnings if probe.session_freshness != "fresh" else []),
        )
