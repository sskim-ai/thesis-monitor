from fastapi import APIRouter

from app.providers.registry import provider_statuses
from app.schemas.provider import ProviderStatusResponse

router = APIRouter()


@router.get(
    "/provider-status",
    response_model=list[ProviderStatusResponse],
    operation_id="getProviderStatus",
)
def get_provider_status() -> list[ProviderStatusResponse]:
    return [ProviderStatusResponse(**status.__dict__) for status in provider_statuses()]
