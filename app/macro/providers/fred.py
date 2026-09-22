from datetime import datetime, timezone

import httpx

from app.config import get_settings
from app.macro.providers.base import CollectedObservation, MacroProviderResult
from app.macro.publication import PUBLICATION_SERIES, publication_receipt, publication_current


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
                    rows = response.json().get("observations", [])
                    valid_rows = [item for item in rows if item.get("value") != "."][:2]
                    if not valid_rows:
                        result.warnings.append(f"{series_code}: no current observation")
                        continue
                    publication, publication_body = None, None
                    if series_code in PUBLICATION_SERIES:
                        try:
                            metadata = await client.get(f"https://fred.stlouisfed.org/series/{series_code}")
                            metadata.raise_for_status()
                            publication_body = metadata.text
                            publication = publication_receipt(metadata.content, series_code, as_of)
                        except (httpx.HTTPError, KeyError, TypeError, ValueError, AttributeError):
                            result.warnings.append(f"{series_code}: publication_metadata_unverified")
                    for row in reversed(valid_rows):
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
                                quality_status=(
                                    'fresh' if publication_current(publication, series_code, row['date'], as_of)
                                    else 'stale'
                                ) if series_code in PUBLICATION_SERIES else None,
                                raw_payload={
                                    "observation_date": row.get("date"),
                                    "realtime_start": row.get("realtime_start"),
                                    "realtime_end": row.get("realtime_end"),
                                    "publication_receipt": publication,
                                    "publication_metadata_html": publication_body,
                                },
                            )
                        )
                except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                    result.warnings.append(f"{series_code}: {type(exc).__name__}")
        return result
