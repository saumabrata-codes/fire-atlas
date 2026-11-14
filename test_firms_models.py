from datetime import date

import pytest

from backend.app.ingestion.firms.models import (
    FireObservation,
    ObservationValidationError
)


@pytest.fixture
def sample_row():
    return {
        "latitude": "22.5726",
        "longitude": "88.3639",
        "brightness": "325.4",
        "scan": "0.5",
        "track": "0.4",
        "acq_date": "2026-11-10",
        "acq_time": "1830",
        "satellite": "N",
        "instrument": "VIIRS",
        "confidence": "high",
        "version": "2.0",
        "bright_t31": "290.5",
        "frp": "12.5",
        "daynight": "N"
    }


def test_observation_creation(sample_row):

    observation = FireObservation.from_firms_row(
        sample_row,
        source_dataset="VIIRS_SNPP_SP"
    )

    assert observation.latitude == 22.5726
    assert observation.longitude == 88.3639
    assert observation.source_dataset == "VIIRS_SNPP_SP"
    assert observation.frp == 12.5
    assert observation.acquisition_date == date(2026, 11, 10)


def test_observation_to_dict(sample_row):

    observation = FireObservation.from_firms_row(
        sample_row,
        source_dataset="VIIRS_SNPP_SP"
    )

    result = observation.to_dict()

    assert isinstance(result, dict)
    assert result["latitude"] == 22.5726
    assert result["longitude"] == 88.3639


def test_invalid_latitude_rejected():

    with pytest.raises(ObservationValidationError):

        FireObservation(
            latitude=120,
            longitude=88,
            acquisition_date=date(2026, 11, 10),
            acquisition_time="1830",
            satellite="N",
            instrument="VIIRS",
            source_dataset="VIIRS_SNPP_SP"
        )