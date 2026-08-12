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
            observed_at = datetime.combine(item.source_date, time.min, tzinfo=KST)
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
                    raw_payload={
                        "product": item.product,
                        "contract_code": item.contract_code,
                        "contract_name": item.contract_name,
                        "expiry": item.maturity,
                        "trade_date": item.source_date.isoformat(),
                        "night_close": item.night_close,
                        "regular_close": item.regular_close,
                        "point_change": item.point_change,
                        "change_pct": item.change_pct,
                        "session_evidence": item.session_evidence,
                    },
                )
            )
        return MacroProviderResult(provider=self.name, observations=observations)
