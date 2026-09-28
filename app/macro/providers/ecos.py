from datetime import datetime, timezone
from math import isfinite

import httpx

from app.config import get_settings
from app.macro.providers.base import CollectedObservation, MacroProviderResult
from app.services.macro_source_time import publication_context, observed_timestamp


KEY_STAT_FILTERS = {
    "한국은행 기준금리": ("BOK_BASE_RATE", "rates"),
    "원/달러 환율": ("USDKRW", "fx"),
    "소비자물가지수": ("KR_CPI", "inflation"),
    "M2": ("KR_M2", "liquidity"),
}


class EcosProvider:
    name = "ecos"

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport

    async def collect(self, as_of: datetime) -> MacroProviderResult:
        result = MacroProviderResult(provider=self.name)
        if not self.settings.ecos_api_key:
            result.warnings.append("ECOS_API_KEY is not configured")
            return result

        url = f"https://ecos.bok.or.kr/api/KeyStatisticList/{self.settings.ecos_api_key}/json/kr/1/100"
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.macro_provider_timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                retrieved_at = datetime.now(timezone.utc)
            rows = response.json().get("KeyStatisticList", {}).get("row", [])
            for name_fragment, (series_code, category) in KEY_STAT_FILTERS.items():
                matches = [item for item in rows if name_fragment in str(item.get("KEYSTAT_NAME", ""))]
                if len(matches) != 1:
                    result.warnings.append(f"{series_code}: missing_or_ambiguous_key_statistic")
                    continue
                row = matches[0]
                try:
                    value = float(str(row["DATA_VALUE"]).replace(",", ""))
                    if not isfinite(value):
                        raise ValueError("nonfinite_source_value")
                    temporal = publication_context(provider=self.name, series=series_code,
                        period=row.get("TIME"), query_as_of=as_of, retrieved_at=retrieved_at,
                        response_bytes=response.content, cadence=str(row.get("CYCLE") or "source_period"),
                        latest_verified=True, daily_required=series_code == "USDKRW")
                except ValueError:
                    result.warnings.append(f"{series_code}: source_observation_period_unavailable")
                    continue
                result.observations.append(
                    CollectedObservation(
                        series_code=series_code,
                        category=category,
                        observed_at=observed_timestamp(temporal),
                        value=value,
                        unit=str(row.get("UNIT_NAME") or "") or None,
                        frequency=str(row.get("CYCLE") or "") or None,
                        source_url="https://ecos.bok.or.kr/",
                        raw_payload={"name": row.get("KEYSTAT_NAME"), "source_period": row.get("TIME"),
                                     "publication_context": temporal},
                    )
                )
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            result.warnings.append(f"KeyStatisticList: {type(exc).__name__}")
        return result
