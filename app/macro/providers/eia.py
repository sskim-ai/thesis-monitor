from datetime import datetime, timezone
from math import isfinite

import httpx

from app.config import get_settings
from app.macro.providers.base import CollectedObservation, MacroProviderResult
from app.services.macro_source_time import publication_context


EIA_SERIES = {
    "PET.WCESTUS1.W": ("WCESTUS1", "crude_inventory", "thousand_barrels"),
    "PET.WCRFPUS2.W": ("WCRFPUS2", "crude_production", "thousand_barrels_per_day"),
    "PET.WPULEUS3.W": ("WPULEUS3", "refinery_utilization", "percent"),
}


class EiaProvider:
    name = "eia"

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport

    async def collect(self, as_of: datetime) -> MacroProviderResult:
        result = MacroProviderResult(provider=self.name)
        if not self.settings.eia_api_key:
            result.warnings.append("EIA_API_KEY is not configured")
            return result

        async with httpx.AsyncClient(
            base_url="https://api.eia.gov",
            timeout=self.settings.macro_provider_timeout_seconds,
            transport=self.transport,
        ) as client:
            for series_id, (series_code, category, fallback_unit) in EIA_SERIES.items():
                try:
                    response = await client.get(
                        f"/v2/seriesid/{series_id}",
                        params={
                            "api_key": self.settings.eia_api_key,
                            "length": 1,
                        },
                    )
                    response.raise_for_status()
                    retrieved_at = datetime.now(timezone.utc)
                    rows = response.json().get("response", {}).get("data", [])
                    if not rows:
                        result.warnings.append(f"{series_code}: no current observation")
                        continue
                    row = rows[0]
                    value = float(row["value"])
                    if not isfinite(value):
                        raise ValueError("nonfinite_source_value")
                    observed_at = datetime.fromisoformat(str(row["period"])).replace(
                        tzinfo=timezone.utc
                    )
                    temporal = publication_context(provider=self.name, series=series_code,
                        period=row["period"], query_as_of=as_of, retrieved_at=retrieved_at,
                        response_bytes=response.content, cadence="weekly", latest_verified=False,
                        daily_required=True)
                    result.observations.append(
                        CollectedObservation(
                            series_code=series_code,
                            category=category,
                            observed_at=observed_at,
                            value=value,
                            unit=str(row.get("units") or fallback_unit),
                            frequency="weekly",
                            source_url="https://www.eia.gov/petroleum/supply/weekly/",
                            raw_payload={"series_id": series_id, "source_period": row["period"],
                                         "publication_context": temporal},
                        )
                    )
                except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                    result.warnings.append(f"{series_code}: {type(exc).__name__}")
        return result
