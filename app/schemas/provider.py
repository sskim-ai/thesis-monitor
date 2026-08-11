from pydantic import BaseModel


class ProviderStatusResponse(BaseModel):
    name: str
    enabled: bool
    configured: bool
    required_settings: list[str]
    mode: str
    markets: list[str] = []
    asset_types: list[str] = []
    supported_data: list[str] = []
    freshness_expectation: str = "unknown"
    historical_depth_years: int | None = None
    forward_data_available: bool = False
