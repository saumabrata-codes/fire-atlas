from datetime import date
from unittest.mock import MagicMock, Mock

import pytest
import requests

from app.ingestion.firms import availability as availability_module
from app.ingestion.firms.availability import DatasetAvailability


@pytest.fixture(autouse=True)
def isolated_availability(monkeypatch):
    """
    Prevent dynamic state from leaking into other tests.

    Monkeypatch restores the original class attribute after each test.
    """
    monkeypatch.setattr(DatasetAvailability, "_active_datasets", None)


@pytest.fixture
def valid_csv():
    """Build a complete sample response for all supported datasets."""
    lines = ["data_id,min_date,max_date"]

    for source, info in DatasetAvailability.DATASETS.items():
        first = info["first_available"].isoformat()
        last = info["last_available"].isoformat()

        if source == "MODIS_NRT":
            last = "2026-11-14"

        lines.append(f"{source},{first},{last}")

    return "\n".join(lines) + "\n"


@pytest.fixture
def mock_get(monkeypatch):
    """Replace HTTP completely: these tests never contact NASA."""
    response = MagicMock()
    response.__enter__.return_value = response
    response.__exit__.return_value = False

    get = Mock(return_value=response)
    monkeypatch.setattr(availability_module.requests, "get", get)

    return get, response


def test_static_fallback_without_network(mock_get):
    get, _ = mock_get

    assert len(DatasetAvailability.get_all_datasets()) == 8
    assert DatasetAvailability.get_dataset_info(
        "MODIS_NRT"
    )["last_available"] == date(2026, 11, 12)

    get.assert_not_called()


def test_successful_refresh_all_eight_datasets(valid_csv, mock_get):
    get, response = mock_get
    response.text = valid_csv

    assert DatasetAvailability.refresh_from_nasa(
        api_key="test-key"
    ) is True

    assert len(DatasetAvailability.get_all_datasets()) == 8

    assert DatasetAvailability.get_dataset_info(
        "MODIS_NRT"
    )["last_available"] == date(2026, 11, 14)

    assert DatasetAvailability.is_date_available(
        "MODIS_NRT", date(2026, 11, 14)
    )

    assert "MODIS_NRT" in DatasetAvailability.get_available_sources(
        date(2026, 11, 14), date(2026, 11, 14)
    )

    # Static fallback must not be overwritten.
    assert DatasetAvailability.DATASETS[
        "MODIS_NRT"
    ]["last_available"] == date(2026, 11, 12)

    get.assert_called_once_with(
        f"{DatasetAvailability.AVAILABILITY_URL}/test-key/ALL",
        timeout=30,
    )
    response.raise_for_status.assert_called_once()


def test_unknown_products_are_ignored(valid_csv, mock_get):
    _, response = mock_get
    response.text = (
        valid_csv
        + "LANDSAT_NRT,2022-06-20,2026-11-14\n"
        + "GOES_NRT,2022-08-09,2026-11-14\n"
    )

    assert DatasetAvailability.refresh_from_nasa("test-key")
    assert set(DatasetAvailability.get_all_datasets()) == set(
        DatasetAvailability.DATASETS
    )


@pytest.mark.parametrize(
    "bad_csv",
    [
        "",
        "Invalid MAP_KEY",
        "source,start,end\nMODIS_NRT,2026-09-01,2026-11-14\n",
        "data_id,min_date,max_date\n",
        "data_id,min_date,max_date\nMODIS_NRT,2026-09-01,2026-11-14\n",
    ],
    ids=[
        "empty-body",
        "error-text",
        "wrong-headers",
        "headers-only",
        "incomplete-datasets",
    ],
)
def test_invalid_response_keeps_static_fallback(bad_csv, mock_get):
    _, response = mock_get
    response.text = bad_csv
    before = DatasetAvailability.get_all_datasets()

    assert DatasetAvailability.refresh_from_nasa("test-key") is False
    assert DatasetAvailability.get_all_datasets() == before


@pytest.mark.parametrize(
    "replacement",
    [
        "MODIS_NRT,not-a-date,2026-11-14",
        "MODIS_NRT,2026-09-01,",
        "MODIS_NRT,2026-11-15,2026-11-14",
        "MODIS_NRT,20260901,2026-11-14",
        "MODIS_NRT,2026-09-01,2026-11-14,unexpected",
    ],
    ids=[
        "invalid-date",
        "missing-date",
        "reversed-range",
        "noncanonical-date",
        "extra-row-value",
    ],
)
def test_bad_supported_row_rejects_entire_refresh(
    replacement, valid_csv, mock_get
):
    _, response = mock_get
    response.text = valid_csv.replace(
        "MODIS_NRT,2026-09-01,2026-11-14",
        replacement,
    )
    before = DatasetAvailability.get_all_datasets()

    assert DatasetAvailability.refresh_from_nasa("test-key") is False
    assert DatasetAvailability.get_all_datasets() == before


def test_duplicate_supported_dataset_is_rejected(valid_csv, mock_get):
    _, response = mock_get
    response.text = (
        valid_csv + "MODIS_NRT,2026-09-01,2026-11-14\n"
    )

    assert DatasetAvailability.refresh_from_nasa("test-key") is False
    assert DatasetAvailability._active_datasets is None


@pytest.mark.parametrize(
    "error_type",
    [
        requests.Timeout,
        requests.ConnectionError,
        requests.HTTPError,
    ],
)
def test_request_failures_keep_fallback_without_key_leak(
    error_type, mock_get, caplog
):
    get, response = mock_get
    secret = "secret-test-key"
    error = error_type(f"Failure for URL containing {secret}")

    if error_type is requests.HTTPError:
        response.raise_for_status.side_effect = error
    else:
        get.side_effect = error

    before = DatasetAvailability.get_all_datasets()

    assert DatasetAvailability.refresh_from_nasa(secret) is False
    assert DatasetAvailability.get_all_datasets() == before
    assert secret not in caplog.text


def test_failed_refresh_retains_previous_dynamic_snapshot(
    valid_csv, mock_get
):
    get, response = mock_get
    response.text = valid_csv

    assert DatasetAvailability.refresh_from_nasa("test-key")
    before = DatasetAvailability.get_all_datasets()

    get.side_effect = requests.Timeout("Simulated timeout")

    assert DatasetAvailability.refresh_from_nasa("test-key") is False
    assert DatasetAvailability.get_all_datasets() == before
    assert before["MODIS_NRT"]["last_available"] == date(2026, 11, 14)


def test_lookup_returns_copies(valid_csv, mock_get):
    _, response = mock_get
    response.text = valid_csv
    assert DatasetAvailability.refresh_from_nasa("test-key")

    info = DatasetAvailability.get_dataset_info("MODIS_NRT")
    info["last_available"] = date(2000, 1, 1)

    datasets = DatasetAvailability.get_all_datasets()
    datasets["MODIS_NRT"]["last_available"] = date(2001, 1, 1)

    assert DatasetAvailability.get_dataset_info(
        "MODIS_NRT"
    )["last_available"] == date(2026, 11, 14)


def test_missing_configured_key_makes_no_request(monkeypatch, mock_get):
    get, _ = mock_get

    def missing_key():
        raise ValueError("Missing configuration")

    monkeypatch.setattr(
        availability_module, "get_firms_api_key", missing_key
    )

    assert DatasetAvailability.refresh_from_nasa() is False
    get.assert_not_called()


def test_configured_key_is_used(monkeypatch, valid_csv, mock_get):
    get, response = mock_get
    response.text = valid_csv

    monkeypatch.setattr(
        availability_module,
        "get_firms_api_key",
        lambda: "configured-test-key",
    )

    assert DatasetAvailability.refresh_from_nasa() is True

    get.assert_called_once_with(
        f"{DatasetAvailability.AVAILABILITY_URL}/configured-test-key/ALL",
        timeout=30,
    )


@pytest.mark.parametrize("timeout", [0, -1, True, 1.5, "30"])
def test_invalid_timeout_is_rejected(timeout, mock_get):
    get, _ = mock_get

    with pytest.raises(ValueError, match="timeout"):
        DatasetAvailability.refresh_from_nasa(
            "test-key", timeout=timeout
        )

    get.assert_not_called()
