"""Health route."""
from fastapi import APIRouter

from backend.app.api.schemas import ApiStatus

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=ApiStatus)
def healthcheck() -> ApiStatus:
    return ApiStatus(status="ok")
