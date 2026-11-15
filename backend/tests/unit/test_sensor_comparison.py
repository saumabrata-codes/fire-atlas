
import pytest

from app.analytics.sensor_comparison.calculations import (
    calculate_sensor_comparison,
)


@pytest.fixture
def sample_observations():
    return [
        {
            "instrument": "MODIS",
            "acquisition_date": "2026-11-10",
            "source_dataset": "MODIS_SP",
            "frp": 12.4,
        },
        {
            "instrument": "MODIS",
            "acquisition_date": "2026-11-11",
            "source_dataset": "MODIS_SP",
            "frp": 18.7,
        },
        {
            "instrument": "MODIS",
            "acquisition_date": "2026-11-12",
            "source_dataset": "MODIS_SP",
            "frp": 9.6,
        },
        {
            "instrument": "VIIRS",
            "acquisition_date": "2026-11-10",
            "source_dataset": "VIIRS_SNPP_SP",
            "frp": 7.8,
        },
        {
            "instrument": "VIIRS",
            "acquisition_date": "2026-11-11",
            "source_dataset": "VIIRS_SNPP_SP",
            "frp": 14.2,
        },
        {
            "instrument": "VIIRS",
            "acquisition_date": "2026-11-12",
            "source_dataset": "VIIRS_SNPP_SP",
            "frp": 5.3,
        },
    ]


def test_sensor_counts_and_percentages(sample_observations):
    result = calculate_sensor_comparison(
        sample_observations, "daily"
    )

    assert result["total_hotspot_detections"] == 6
    assert result["sensor_counts"]["MODIS"] == 3
    assert result["sensor_counts"]["VIIRS"] == 3

    assert result["sensor_summaries"]["MODIS"][
        "detection_share_percent"
    ] == 50.0


def test_frp_statistics(sample_observations):
    result = calculate_sensor_comparison(
        sample_observations, "daily"
    )

    assert round(
        result["sensor_summaries"]["MODIS"]["mean_frp_mw"], 2
    ) == 13.57

    assert result["sensor_summaries"]["MODIS"]["max_frp_mw"] == 18.7

    assert result["sensor_summaries"]["VIIRS"]["mean_frp_mw"] == 9.1


def test_daily_time_series(sample_observations):
    result = calculate_sensor_comparison(
        sample_observations, "daily"
    )

    assert len(result["time_series"]) == 3
    assert result["time_series"][0] == {
        "period": "2026-11-10",
        "MODIS": 1,
        "VIIRS": 1,
        "total_detections": 2,
    }


def test_monthly_time_series(sample_observations):
    result = calculate_sensor_comparison(
        sample_observations, "monthly"
    )

    assert len(result["time_series"]) == 1
    assert result["time_series"][0]["period"] == "2026-11"
    assert result["time_series"][0]["total_detections"] == 6


def test_yearly_time_series(sample_observations):
    result = calculate_sensor_comparison(
        sample_observations, "yearly"
    )

    assert result["time_series"][0]["period"] == "2026"


def test_product_summaries(sample_observations):
    result = calculate_sensor_comparison(
        sample_observations, "daily"
    )

    assert len(result["product_summaries"]) == 2


def test_missing_frp_is_excluded_from_frp_statistics():
    observations = [
        {
            "instrument": "MODIS",
            "acquisition_date": "2026-11-10",
            "source_dataset": "MODIS_SP",
            "frp": None,
        }
    ]

    result = calculate_sensor_comparison(observations, "daily")

    assert result["sensor_counts"]["MODIS"] == 1
    assert result["sensor_summaries"]["MODIS"]["mean_frp_mw"] is None
    assert result["sensor_summaries"]["MODIS"]["observations_with_frp"] == 0


def test_empty_observations():
    result = calculate_sensor_comparison([], "daily")

    assert result["total_hotspot_detections"] == 0
    assert result["sensor_counts"] == {"MODIS": 0, "VIIRS": 0}
    assert result["time_series"] == []


def test_invalid_sensor_is_rejected():
    observations = [
        {
            "instrument": "UNKNOWN",
            "acquisition_date": "2026-11-10",
            "source_dataset": "UNKNOWN",
            "frp": 10,
        }
    ]

    with pytest.raises(ValueError):
        calculate_sensor_comparison(observations, "daily")


def test_negative_frp_is_rejected():
    observations = [
        {
            "instrument": "MODIS",
            "acquisition_date": "2026-11-10",
            "source_dataset": "MODIS_SP",
            "frp": -5,
        }
    ]

    with pytest.raises(ValueError):
        calculate_sensor_comparison(observations, "daily")
