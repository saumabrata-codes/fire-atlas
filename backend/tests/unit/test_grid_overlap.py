import pytest

from app.analytics.harmonization.grid_overlap import (
    assign_grid_cell,
    calculate_grid_overlap,
    analyze_grid_sensitivity,
)


def test_grid_overlap_classifies_shared_and_sensor_only_cells():
    rows = [
        {"longitude": 10, "latitude": 20, "acquisition_date": "2025-01-01", "instrument": "MODIS"},
        {"longitude": 10.001, "latitude": 20.001, "acquisition_date": "2025-01-01", "instrument": "VIIRS"},
        {"longitude": 30, "latitude": 40, "acquisition_date": "2025-01-01", "instrument": "MODIS"},
        {"longitude": 50, "latitude": 60, "acquisition_date": "2025-01-01", "instrument": "VIIRS"},
    ]

    result = calculate_grid_overlap(rows, 1000)

    assert result["total_grid_days"] == 3
    assert result["shared"] == 1
    assert result["modis_only"] == 1
    assert result["viirs_only"] == 1
    assert result["overlap_percent"] == 33.33


def test_same_location_on_different_dates_is_a_different_grid_day():
    rows = [
        {"longitude": 10, "latitude": 20, "acquisition_date": "2025-01-01", "instrument": "MODIS"},
        {"longitude": 10, "latitude": 20, "acquisition_date": "2025-01-02", "instrument": "VIIRS"},
    ]

    result = calculate_grid_overlap(rows, 1000)

    assert result["total_grid_days"] == 2
    assert result["shared"] == 0


def test_grid_size_must_be_positive():
    with pytest.raises(ValueError):
        assign_grid_cell(10, 20, 0)


def test_invalid_coordinates_are_rejected():
    with pytest.raises(ValueError):
        assign_grid_cell(200, 20, 1000)


def test_unsupported_sensor_is_rejected():
    rows = [
        {"longitude": 10, "latitude": 20, "acquisition_date": "2025-01-01", "instrument": "OTHER"},
    ]

    with pytest.raises(ValueError, match="Unsupported sensor"):
        calculate_grid_overlap(rows, 1000)


def test_empty_input_returns_zero_overlap():
    result = calculate_grid_overlap([], 1000)

    assert result["total_grid_days"] == 0
    assert result["shared"] == 0
    assert result["overlap_percent"] == 0.0


def test_sensitivity_runs_all_requested_resolutions():
    rows = [
        {"longitude": 10, "latitude": 20, "acquisition_date": "2025-01-01", "instrument": "MODIS"},
        {"longitude": 10.001, "latitude": 20.001, "acquisition_date": "2025-01-01", "instrument": "VIIRS"},
    ]

    results = analyze_grid_sensitivity(rows, (1000, 5000, 10000))

    assert [item["grid_size_m"] for item in results] == [1000, 5000, 10000]
    assert all(item["total_grid_days"] >= 1 for item in results)
