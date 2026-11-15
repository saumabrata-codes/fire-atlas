
from fastapi import APIRouter

from app.api.v1.schemas.filters import DataFilter
from app.api.v1.schemas.overview import OverviewResponse
from app.application.overview_service import build_overview

router = APIRouter()


@router.post(
    "/overview",
    response_model=OverviewResponse,
    tags=["Overview"],
)
async def get_overview(filters: DataFilter):
    """
    Return aggregated hotspot activity for the selected filters.
    """

    return build_overview(filters)
