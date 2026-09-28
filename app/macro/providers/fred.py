from datetime import datetime, timezone
from math import isfinite

import httpx

from app.config import get_settings
from app.macro.providers.base import CollectedObservation, MacroProviderResult
from app.services.macro_source_time import publication_context


FRED_SERIES = {
    "DGS2": ("rates", "percent", "daily"),
    "DGS3": ("rates", "percent", "daily"),
    "DGS5": ("rates", "percent", "daily"),
    "DGS10": ("rates", "percent", "daily"),
    "DGS30": ("rates", "percent", "daily"),
    "DFII10": ("real_rates", "percent", "daily"),
    "T10YIE": ("inflation_expectations", "percent", "daily"),
    "BAMLH0A0HYM2": ("credit", "percent", "daily"),
    "VIXCLS": ("volatility", "index", "daily"),
    "DCOILWTICO": ("commodities", "usd_per_barrel", "daily"),
    "DTWEXBGS": ("fx", "index", "daily"),
    "WALCL": ("liquidity", "millions_usd", "weekly"),
    "RRPONTSYD": ("liquidity", "billions_usd", "daily"),
}


class FredProvider:
    name = "fred"

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport

    async def collect(self, as_of: datetime) -> MacroProviderResult:
        result = MacroProviderResult(provider=self.name)
        if not self.settings.fred_api_key:
            result.warnings.append("FRED_API_KEY is not configured")
            return result

        async with httpx.AsyncClient(
            base_url="https://api.stlouisfed.org",
            timeout=self.settings.macro_provider_timeout_seconds,
            transport=self.transport,
        ) as client:
            for series_code, (category, unit, frequency) in FRED_SERIES.items():
                try:
                    response = await client.get(
                        "/fred/series/observations",
                        params={
                            "series_id": series_code,
                            "api_key": self.settings.fred_api_key,
                            "file_type": "json",
                            "sort_order": "desc",
                            "limit": 5,
                            "observation_end": as_of.date().isoformat(),
                        },
                    )
                    response.raise_for_status()
                    retrieved_at = datetime.now(timezone.utc)
                    rows = response.json().get("observations", [])
                    qualified = [item for item in rows if item.get("value") not in {None, "."}]
                    if (len({r['date'] for r in qualified}) != len(qualified)
                            or any(not isfinite(float(r['value'])) for r in qualified)):
                        raise ValueError("ambiguous_or_nonfinite_observation")
                    valid_rows = sorted(qualified, key=lambda item: item["date"], reverse=True)[:2]
                    if not valid_rows:
                        result.warnings.append(f"{series_code}: no current observation")
                        continue
                    for row in reversed(valid_rows):
                        temporal = publication_context(provider=self.name, series=series_code,
                            period=row["date"], query_as_of=as_of, retrieved_at=retrieved_at,
                            response_bytes=response.content, cadence=frequency,
                            latest_verified=row == valid_rows[0], daily_required=True)
                        observed_at = datetime.fromisoformat(str(row["date"])).replace(
                            tzinfo=timezone.utc
                        )
                        result.observations.append(
                            CollectedObservation(
                                series_code=series_code,
                                category=category,
                                observed_at=observed_at,
                                value=float(row["value"]),
                                unit=unit,
                                frequency=frequency,
                                source_url=f"https://fred.stlouisfed.org/series/{series_code}",
                                raw_payload={
                                    "observation_date": row.get("date"),
                                    "realtime_start": row.get("realtime_start"),
                                    "realtime_end": row.get("realtime_end"),
                                    "publication_context": temporal,
                                },
                            )
                        )
                except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                    result.warnings.append(f"{series_code}: {type(exc).__name__}")
        return result
