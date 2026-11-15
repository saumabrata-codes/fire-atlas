
import pytest
from pydantic import ValidationError

from app.api.v1.schemas.filters import DataFilter
from app.api.v1.schemas.responses import (
    ActiveFireDataResponse,
    DataStatus,
)


def test_global_filter_is_valid():
    data = DataFilter.model_validate({
        "start_date": "2026-11-10",
        "end_date": "2026-11-12",
        "geography": {
            "selection_type": "global"
        },
        "sensors": ["MODIS", "VIIRS"],
        "aggregation": "daily",
    })

    assert data.geography.selection_type == "global"
    assert data.geography.bbox is None


def test_bounding_box_filter_is_valid():
    data = DataFilter.model_validate({
        "start_date": "2026-11-10",
        "end_date": "2026-11-12",
        "geography": {
            "selection_type": "bounding_box",
            "bbox": {
                "west": 85,
                "south": 20,
                "east": 90,
                "north": 25,
            },
        },
    })

    assert data.geography.bbox.west == 85


def test_global_filter_rejects_bbox():
    with pytest.raises(ValidationError):
        DataFilter.model_validate({
            "start_date": "2026-11-10",
            "end_date": "2026-11-12",
            "geography": {
                "selection_type": "global",
                "bbox": {
                    "west": 85,
                    "south": 20,
                    "east": 90,
                    "north": 25,
                },
            },
        })


def test_bounding_box_requires_coordinates():
    with pytest.raises(ValidationError):
        DataFilter.model_validate({
            "start_date": "2026-11-10",
            "end_date": "2026-11-12",
            "geography": {
                "selection_type": "bounding_box"
            },
        })


def test_invalid_date_range_is_rejected():
    with pytest.raises(ValidationError):
        DataFilter.model_validate({
            "start_date": "2026-11-12",
            "end_date": "2026-11-10",
            "geography": {
                "selection_type": "global"
            },
        })


def test_response_schema_accepts_empty_results():
    response = ActiveFireDataResponse.model_validate({
        "records": [],
        "metadata": {
            "provider": "mock",
            "is_synthetic": True,
            "requested_start_date": "2026-11-10",
            "requested_end_date": "2026-11-12",
            "sensors_requested": ["MODIS", "VIIRS"],
            "records_returned": 0,
            "sensor_record_counts": {
                "MODIS": 0,
                "VIIRS": 0,
            },
            "data_status": DataStatus.NO_DATA,
            "note": "Synthetic test data.",
        },
    })

    assert response.metadata.records_returned == 0
