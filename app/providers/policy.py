from dataclasses import dataclass

from app.config import get_settings


@dataclass(frozen=True)
class ProviderPolicy:
    data_type: str
    market: str
    providers: tuple[str, ...]


class ProviderPolicyRegistry:
    def policies(self) -> list[ProviderPolicy]:
        return [
            ProviderPolicy("financial_statements", "KR", ("opendart", "company_ir")),
            ProviderPolicy("financial_statements", "US", ("sec_edgar", "alpha_vantage", "fmp")),
            ProviderPolicy("financial_statements", "foreign", ("sec_edgar", "company_ir", "fmp")),
            ProviderPolicy("consensus", "global", ("finnhub", "alpha_vantage", "fmp", "internal_model")),
            ProviderPolicy("dividend", "KR", ("opendart", "company_ir")),
            ProviderPolicy("dividend", "US", ("sec_edgar", "alpha_vantage", "fmp")),
            ProviderPolicy("shares", "KR", ("opendart",)),
            ProviderPolicy("shares", "US", ("sec_edgar", "alpha_vantage", "fmp")),
            ProviderPolicy("corporate_actions", "KR", ("opendart",)),
            ProviderPolicy("corporate_actions", "US", ("sec_edgar", "company_ir", "alpha_vantage", "fmp")),
            ProviderPolicy("price", "global", ("ohlcv_analyst", "alpha_vantage")),
            ProviderPolicy("identity", "global", ("official_filing", "openfigi")),
            ProviderPolicy("historical_point_in_time", "US", ("internal_point_in_time", "sharadar")),
        ]

    def optional_statuses(self) -> dict[str, dict[str, object]]:
        settings = get_settings()
        return {
            "openfigi": {
                "configured": bool(settings.openfigi_api_key),
                "enabled": True,
                "role": "identity_mapping",
            },
            "fmp": {
                "configured": bool(settings.fmp_api_key),
                "enabled": bool(settings.fmp_api_key),
                "role": "secondary_fundamentals_consensus",
            },
            "sharadar": {
                "configured": bool(settings.sharadar_api_key),
                "enabled": bool(settings.sharadar_api_key),
                "role": "historical_point_in_time_validation",
            },
        }
