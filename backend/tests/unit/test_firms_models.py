
from datetime import date, datetime

import pytest

from app.ingestion.firms.models import (
    FireObservation,
    ObservationValidationError,
)


def make_observation(**overrides):
    values = {
        "latitude": 22.5726,
        "longitude": 88.3639,
        "acquisition_date": date(2025, 1, 1),
        "acquisition_time": "1200",
        "satellite": "Terra",
        "instrument": "MODIS",
        "source_dataset": "MODIS_SP",
        "frp": 12.5,
    }
    values.update(overrides)
    return FireObservation(**values)


def test_valid_observation():
    observation = make_observation()
    assert observation.instrument == "MODIS"
    assert observation.frp == 12.5


@pytest.mark.parametrize(
    "field,value",
    [
        ("latitude", 91),
        ("latitude", -91),
        ("longitude", 181),
        ("longitude", -181),
        ("latitude", float("nan")),
        ("longitude", float("inf")),
        ("frp", -1),
        ("frp", float("nan")),
        ("frp", float("inf")),
        ("acquisition_date", datetime(2025, 1, 1)),
    ],
)
def test_invalid_observation_values(field, value):
    with pytest.raises(ObservationValidationError):
        make_observation(**{field: value})


def test_missing_source_dataset():
    with pytest.raises(ObservationValidationError):
        make_observation(source_dataset="")


def test_to_dict_preserves_sensor_fields():
    observation = make_observation(
        bright_ti4=310.2,
        confidence="nominal",
    )

    result = observation.to_dict()

    assert result["bright_ti4"] == 310.2
    assert result["confidence"] == "nominal"
    assert result["source_dataset"] == "MODIS_SP"
