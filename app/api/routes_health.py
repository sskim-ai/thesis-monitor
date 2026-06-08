from fastapi import APIRouter

router = APIRouter()


@router.get("/health", operation_id="getHealth")
def get_health() -> dict[str, str]:
    return {"status": "ok"}

