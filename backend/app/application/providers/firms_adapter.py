
import os
from datetime import date
from typing import Any

from app.application.mock_data_provider import (
    get_active_fire_data as get_mock_fire_data,
)
from app.ingestion.firms.availability import DatasetAvailability
from app.ingestion.firms.provider import HistoricalFireDataProvider


def _get_area(
    bbox: tuple[float, float, float, float] | None,
) -> str:
    if bbox is None:
        return "world"

    return ",".join(str(value) for value in bbox)


def _get_requested_sources(
    start_date: date,
    end_date: date,
    sensors: list[str] | None,
) -> list[str]:
    selected_sensors = {
        sensor.upper()
        for sensor in (sensors or ["MODIS", "VIIRS"])
    }

    valid_sensors = {"MODIS", "VIIRS"}

    if not selected_sensors.issubset(valid_sensors):
        raise ValueError("Supported sensors are MODIS and VIIRS.")

    datasets = DatasetAvailability.get_all_datasets()

    return [
        source
        for source, info in datasets.items()
        if info["satellite"].split("_")[0] in selected_sensors
        and start_date <= info["last_available"]
        and end_date >= info["first_available"]
    ]


def _get_nasa_data(
    start_date: date,
    end_date: date,
    bbox: tuple[float, float, float, float] | None,
    sensors: list[str] | None,
) -> dict[str, Any]:

    requested_sources = _get_requested_sources(
        start_date, end_date, sensors
    )

    sensor_names = sorted({
        sensor.upper()
        for sensor in (sensors or ["MODIS", "VIIRS"])
    })

    if not requested_sources:
        return {
            "records": [],
            "metadata": {
                "provider": "nasa_firms",
                "is_synthetic": False,
                "requested_start_date": start_date.isoformat(),
                "requested_end_date": end_date.isoformat(),
                "sensors_requested": sensor_names,
                "records_returned": 0,
                "sensor_record_counts": {"MODIS": 0, "VIIRS": 0},
                "data_status": "no_matching_records",
                "source_datasets": [],
                "availability_status": "no_dataset_available",
                "note": "No configured NASA dataset overlaps this date range.",
            },
        }

    with HistoricalFireDataProvider() as provider:
        observations = provider.fetch_historical_data(
            area=_get_area(bbox),
            start_date=start_date,
            end_date=end_date,
            sources=requested_sources,
        )
        report = provider.get_report()

    records = []

    for index, observation in enumerate(observations):
        records.append({
            "source_record_id": (
                f"{observation.source_dataset}-"
                f"{observation.acquisition_date}-"
                f"{index}"
            ),
            "sensor": observation.instrument,
            "observed_at": observation.acquisition_date.isoformat(),
            "latitude": observation.latitude,
            "longitude": observation.longitude,
            "frp_mw": observation.frp,
            "source_product": observation.source_dataset,
            "confidence": observation.confidence,
            "is_synthetic": False,
            "source_attributes": observation.to_dict(),
        })

    sensor_counts = {
        sensor: sum(
            1 for record in records
            if record["sensor"] == sensor
        )
        for sensor in ("MODIS", "VIIRS")
    }

    failed = report["failed_requests"]

    if failed:
        status = "partial" if records else "unavailable"
    elif records:
        status = "available"
    else:
        status = "no_matching_records"

    return {
        "records": records,
        "metadata": {
            "provider": "nasa_firms",
            "is_synthetic": False,
            "requested_start_date": start_date.isoformat(),
            "requested_end_date": end_date.isoformat(),
            "sensors_requested": sensor_names,
            "records_returned": len(records),
            "sensor_record_counts": sensor_counts,
            "data_status": status,
            "source_datasets": report["selected_datasets"],
            "availability_status": (
                "dataset_window_selected"
                if report["selected_datasets"]
                else "no_dataset_available"
            ),
            "successful_requests": report["successful_requests"],
            "empty_requests": report["empty_requests"],
            "failed_requests": failed,
            "invalid_observations": report["invalid_observations"],
            "note": (
                "NASA FIRMS retrieval. Dataset availability does not "
                "guarantee observations for every requested date."
            ),
        },
    }


def get_active_fire_data(
    start_date: date,
    end_date: date,
    bbox: tuple[float, float, float, float] | None = None,
    sensors: list[str] | None = None,
) -> dict[str, Any]:

    mode = os.getenv(
        "FIRE_ATLAS_DATA_PROVIDER", "mock"
    ).strip().lower()

    if mode == "mock":
        return get_mock_fire_data(
            start_date=start_date,
            end_date=end_date,
            bbox=bbox,
            sensors=sensors,
        )

    if mode == "nasa":
        return _get_nasa_data(
            start_date=start_date,
            end_date=end_date,
            bbox=bbox,
            sensors=sensors,
        )

    raise ValueError(
        "FIRE_ATLAS_DATA_PROVIDER must be 'mock' or 'nasa'."
    )
