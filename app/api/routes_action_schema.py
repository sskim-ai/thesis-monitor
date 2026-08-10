from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.action_schema import build_action_schema


router = APIRouter()


@router.get("/action-openapi.json", include_in_schema=False)
def get_action_openapi(request: Request) -> JSONResponse:
    return JSONResponse(build_action_schema(request.app))
