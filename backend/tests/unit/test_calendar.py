
import pytest

from app.analytics.temporal.calendar import calculate_calendar


@pytest.fixture
def sample_observations():
    return [
        {
            "instrument": "MODIS",
            "acquisition_date": "2026-11-10",
        },
        {
            "instrument": "MODIS",
            "acquisition_date": "2026-11-11",
        },
        {
            "instrument": "MODIS",
            "acquisition_date": "2026-11-12",
        },
        {
            "instrument": "VIIRS",
            "acquisition_date": "2026-11-10",
        },
        {
            "instrument": "VIIRS",
            "acquisition_date": "2026-11-11",
        },
        {
            "instrument": "VIIRS",
            "acquisition_date": "2026-11-12",
        },
    ]


def test_daily_calendar(sample_observations):
    result = calculate_calendar(sample_observations, "daily")

    assert len(result["calendar_periods"]) == 3
    assert result["calendar_periods"][0] == {
        "period": "2026-11-10",
        "MODIS": 1,
        "VIIRS": 1,
        "total_detections": 2,
        "status": "observed_with_detections",
    }


def test_monthly_calendar(sample_observations):
    result = calculate_calendar(sample_observations, "monthly")

    assert len(result["calendar_periods"]) == 1
    assert result["calendar_periods"][0]["period"] == "2026-11"
    assert result["calendar_periods"][0]["total_detections"] == 6


def test_yearly_calendar(sample_observations):
    result = calculate_calendar(sample_observations, "yearly")

    assert len(result["calendar_periods"]) == 1
    assert result["calendar_periods"][0]["period"] == "2026"
    assert result["calendar_periods"][0]["total_detections"] == 6


def test_sensor_summary(sample_observations):
    result = calculate_calendar(sample_observations, "daily")

    assert result["sensor_summary"] == {
        "MODIS": 3,
        "VIIRS": 3,
    }


def test_activity_summary(sample_observations):
    result = calculate_calendar(sample_observations, "daily")

    summary = result["activity_summary"]

    assert summary["total_detections"] == 6
    assert summary["periods_with_detections"] == 3
    assert summary["highest_activity_period"] == "2026-11-10"
    assert summary["highest_activity_detections"] == 2


def test_empty_observations():
    result = calculate_calendar([], "daily")

    assert result["calendar_periods"] == []
    assert result["activity_summary"]["total_detections"] == 0
    assert result["activity_summary"]["highest_activity_period"] is None


def test_invalid_sensor_is_rejected():
    observations = [
        {
            "instrument": "UNKNOWN",
            "acquisition_date": "2026-11-10",
        }
    ]

    with pytest.raises(ValueError):
        calculate_calendar(observations, "daily")


def test_invalid_aggregation_is_rejected():
    with pytest.raises(ValueError):
        calculate_calendar([], "weekly")
