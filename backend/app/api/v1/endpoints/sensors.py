
from fastapi import APIRouter

from app.api.v1.schemas.filters import DataFilter
from app.api.v1.schemas.sensors import SensorComparisonResponse
from app.application.sensor_comparison_service import (
    build_sensor_comparison,
)


router = APIRouter()


@router.post(
    "/sensors",
    response_model=SensorComparisonResponse,
    summary="Get MODIS and VIIRS sensor comparison",
)
def get_sensor_comparison(
    filters: DataFilter,
) -> SensorComparisonResponse:
    return build_sensor_comparison(filters)
