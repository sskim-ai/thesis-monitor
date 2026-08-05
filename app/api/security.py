from hmac import compare_digest

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import get_settings


action_api_key_header = APIKeyHeader(name="X-Action-API-Key", auto_error=False)


def require_action_api_key(
    x_action_api_key: str | None = Security(action_api_key_header),
) -> None:
    expected = get_settings().action_api_key
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ACTION_API_KEY is not configured on the server.",
        )
    if x_action_api_key is None or not compare_digest(x_action_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid X-Action-API-Key header is required.",
        )
