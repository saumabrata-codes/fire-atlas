
from datetime import date, timedelta

from app.ingestion.firms.availability import DatasetAvailability
from app.ingestion.firms.provider import HistoricalFireDataProvider


def build_sensor_coverage_periods(
    start_date: date,
    end_date: date,
    sources: list[str] | None = None,
) -> list[dict]:
    """Classify date ranges using selected FIRMS dataset availability."""

    if start_date > end_date:
        raise ValueError("start_date cannot be after end_date.")

    selected = HistoricalFireDataProvider._select_sources(
        start_date,
        end_date,
        sources,
    )

    datasets = DatasetAvailability.get_all_datasets()
    daily_periods = []
    current = start_date

    while current <= end_date:
        active_sources = [
            source
            for source, (first, last) in selected.items()
            if first <= current <= last
        ]

        sensors = set()

        for source in active_sources:
            satellite = datasets[source]["satellite"]

            if satellite == "MODIS":
                sensors.add("MODIS")
            elif satellite.startswith("VIIRS"):
                sensors.add("VIIRS")

        if sensors == {"MODIS", "VIIRS"}:
            status = "DUAL_SENSOR"
        elif sensors == {"MODIS"}:
            status = "MODIS_ONLY"
        elif sensors == {"VIIRS"}:
            status = "VIIRS_ONLY"
        else:
            status = "UNAVAILABLE"

        daily_periods.append({
            "start_date": current,
            "end_date": current,
            "status": status,
            "available_sensors": sorted(sensors),
            "available_datasets": sorted(active_sources),
        })

        current += timedelta(days=1)

    # Merge consecutive dates with identical availability.
    periods = []

    for item in daily_periods:
        if (
            periods
            and periods[-1]["status"] == item["status"]
            and periods[-1]["available_sensors"] == item["available_sensors"]
            and periods[-1]["available_datasets"] == item["available_datasets"]
        ):
            periods[-1]["end_date"] = item["end_date"]
        else:
            periods.append(item.copy())

    for period in periods:
        period["start_date"] = period["start_date"].isoformat()
        period["end_date"] = period["end_date"].isoformat()

    return periods
