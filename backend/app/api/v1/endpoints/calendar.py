
from fastapi import APIRouter

from app.api.v1.schemas.filters import DataFilter
from app.api.v1.schemas.calendar import CalendarResponse
from app.application.calendar_service import build_calendar


router = APIRouter()


@router.post(
    "/calendar",
    response_model=CalendarResponse,
    summary="Get fire activity calendar",
)
def get_calendar(
    filters: DataFilter,
) -> CalendarResponse:
    return build_calendar(filters)
