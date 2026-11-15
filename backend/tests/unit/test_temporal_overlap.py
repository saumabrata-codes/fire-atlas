import pytest

from app.analytics.harmonization.temporal_overlap import (
    parse_acquisition_time,
    calculate_temporal_overlap,
)


def row(sensor, time, day="2025-01-01"):
    return {
        "instrument": sensor,
        "acquisition_date": day,
        "acquisition_time": time,
    }


def test_shared_and_sensor_only_bins():
    rows = [
        row("MODIS", "1030"),
        row("VIIRS", "1044"),
        row("MODIS", "1200"),
        row("VIIRS", "1400"),
    ]

    result = calculate_temporal_overlap(rows)

    assert result["total_date_bins"] == 3
    assert result["shared_bins"] == 1
    assert result["modis_only_bins"] == 1
    assert result["viirs_only_bins"] == 1
    assert result["overlap_percent"] == 33.33


def test_bin_boundary_is_correct():
    assert parse_acquisition_time("1029") // 30 == 20
    assert parse_acquisition_time("1030") // 30 == 21
    assert parse_acquisition_time("1100") // 30 == 22


def test_same_bin_on_different_dates_is_separate():
    result = calculate_temporal_overlap([
        row("MODIS", "1030", "2025-01-01"),
        row("VIIRS", "1030", "2025-01-02"),
    ])

    assert result["total_date_bins"] == 2
    assert result["shared_bins"] == 0


def test_invalid_times_are_reported():
    result = calculate_temporal_overlap([
        row("MODIS", "1030"),
        row("VIIRS", "2560"),
        row("MODIS", ""),
    ])

    assert result["invalid_time_count"] == 2
    assert result["sensor_records"] == {"MODIS": 1, "VIIRS": 0}


def test_invalid_time_formats_are_rejected():
    for value in ("", "abc", "2460", "1260", "12345"):
        with pytest.raises(ValueError):
            parse_acquisition_time(value)


def test_unsupported_sensor_is_rejected():
    with pytest.raises(ValueError, match="Unsupported sensor"):
        calculate_temporal_overlap([row("OTHER", "1030")])


def test_invalid_bin_size_is_rejected():
    with pytest.raises(ValueError):
        calculate_temporal_overlap([], 0)


def test_empty_input():
    result = calculate_temporal_overlap([])

    assert result["total_date_bins"] == 0
    assert result["shared_bins"] == 0
    assert result["overlap_percent"] == 0.0


