from pydantic import BaseModel


class ProviderStatusResponse(BaseModel):
    name: str
    enabled: bool
    configured: bool
    required_settings: list[str]
    mode: str
