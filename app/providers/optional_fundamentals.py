from dataclasses import dataclass

from app.config import get_settings


@dataclass(frozen=True)
class OptionalProviderResult:
    provider: str
    status: str
    reason_code: str


class FmpProvider:
    name = "fmp"

    async def coverage(self, _ticker: str) -> OptionalProviderResult:
        configured = bool(get_settings().fmp_api_key)
        return OptionalProviderResult(
            self.name,
            "configured" if configured else "disabled",
            "ready_for_secondary_cross_check" if configured else "api_key_not_configured",
        )


class SharadarProvider:
    name = "sharadar"

    async def coverage(self, _ticker: str) -> OptionalProviderResult:
        configured = bool(get_settings().sharadar_api_key)
        return OptionalProviderResult(
            self.name,
            "configured" if configured else "disabled",
            "ready_for_point_in_time_validation" if configured else "subscription_not_configured",
        )
