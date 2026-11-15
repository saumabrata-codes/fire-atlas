
from datetime import date
from typing import Any


# --------------------------------------------------
# SYNTHETIC TEST DATA
# These are NOT actual NASA FIRMS observations.
# --------------------------------------------------

MOCK_FIRE_RECORDS: list[dict[str, Any]] = [
    {
        "source_record_id": "MOCK-MODIS-001",
        "sensor": "MODIS",
        "observed_at": "2026-11-10",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "frp_mw": 12.4,
        "source_product": "SYNTHETIC_MODIS",
        "is_synthetic": True,
    },
    {
        "source_record_id": "MOCK-MODIS-002",
        "sensor": "MODIS",
        "observed_at": "2026-11-11",
        "latitude": 23.0225,
        "longitude": 72.5714,
        "frp_mw": 18.7,
        "source_product": "SYNTHETIC_MODIS",
        "is_synthetic": True,
    },
    {
        "source_record_id": "MOCK-MODIS-003",
        "sensor": "MODIS",
        "observed_at": "2026-11-12",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "frp_mw": 9.6,
        "source_product": "SYNTHETIC_MODIS",
        "is_synthetic": True,
    },
    {
        "source_record_id": "MOCK-VIIRS-001",
        "sensor": "VIIRS",
        "observed_at": "2026-11-10",
        "latitude": 22.5800,
        "longitude": 88.3700,
        "frp_mw": 7.8,
        "source_product": "SYNTHETIC_VIIRS",
        "is_synthetic": True,
    },
    {
        "source_record_id": "MOCK-VIIRS-002",
        "sensor": "VIIRS",
        "observed_at": "2026-11-11",
        "latitude": 26.1445,
        "longitude": 91.7362,
        "frp_mw": 14.2,
        "source_product": "SYNTHETIC_VIIRS",
        "is_synthetic": True,
    },
    {
        "source_record_id": "MOCK-VIIRS-003",
        "sensor": "VIIRS",
        "observed_at": "2026-11-12",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "frp_mw": 5.3,
        "source_product": "SYNTHETIC_VIIRS",
        "is_synthetic": True,
    },
]


def get_active_fire_data(
    start_date: date,
    end_date: date,
    bbox: tuple[float, float, float, float] | None = None,
    sensors: list[str] | None = None,
) -> dict[str, Any]:
    """
    Retrieve synthetic active-fire records using the same
    interface that the real data provider can implement.

    bbox order: (west, south, east, north)
    """

    if start_date > end_date:
        raise ValueError("start_date cannot be after end_date.")

    if bbox is not None:
        west, south, east, north = bbox

        if not (-180 <= west <= 180 and -180 <= east <= 180):
            raise ValueError("Bounding box longitude must be between -180 and 180.")

        if not (-90 <= south <= 90 and -90 <= north <= 90):
            raise ValueError("Bounding box latitude must be between -90 and 90.")

        if west > east or south > north:
            raise ValueError("Invalid bounding box boundaries.")

    selected_sensors = (
        {sensor.upper() for sensor in sensors}
        if sensors is not None
        else {"MODIS", "VIIRS"}
    )

    valid_sensors = {"MODIS", "VIIRS"}

    if not selected_sensors.issubset(valid_sensors):
        raise ValueError("Supported sensors are MODIS and VIIRS.")

    filtered_records = []

    for record in MOCK_FIRE_RECORDS:
        record_date = date.fromisoformat(record["observed_at"])

        if not (start_date <= record_date <= end_date):
            continue

        if record["sensor"] not in selected_sensors:
            continue

        if bbox is not None:
            west, south, east, north = bbox
            latitude = record["latitude"]
            longitude = record["longitude"]

            if not (
                west <= longitude <= east
                and south <= latitude <= north
            ):
                continue

        filtered_records.append(record.copy())

    sensor_counts = {
        sensor: sum(
            1 for record in filtered_records
            if record["sensor"] == sensor
        )
        for sensor in ("MODIS", "VIIRS")
    }

    return {
        "records": filtered_records,
        "metadata": {
            "provider": "mock",
            "is_synthetic": True,
            "requested_start_date": start_date.isoformat(),
            "requested_end_date": end_date.isoformat(),
            "sensors_requested": sorted(selected_sensors),
            "records_returned": len(filtered_records),
            "sensor_record_counts": sensor_counts,
            "data_status": (
                "available" if filtered_records
                else "no_matching_records"
            ),
            "note": "Synthetic test data. Not actual NASA observations.",
            "source_datasets": [],
"availability_status": None,
"successful_requests": 0,
"empty_requests": 0,
"failed_requests": 0,
"invalid_observations": 0,
        },
    }
