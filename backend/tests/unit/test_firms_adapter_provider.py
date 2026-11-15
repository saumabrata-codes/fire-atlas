
from datetime import date

import pytest

from app.application.providers import firms_adapter
from app.ingestion.firms.client import FirmsApiError
from app.ingestion.firms.models import FireObservation
from app.ingestion.firms.provider import HistoricalFireDataProvider


START = date(2025, 1, 1)
END = date(2025, 1, 1)


def make_observation():
    return FireObservation(
        latitude=22.5726,
        longitude=88.3639,
        acquisition_date=START,
        acquisition_time="1200",
        satellite="Terra",
        instrument="MODIS",
        source_dataset="MODIS_SP",
        frp=12.5,
        confidence="nominal",
        raw_properties={"latitude": "22.5726"},
    )


def make_firms_row():
    return {
        "latitude": "22.5726",
        "longitude": "88.3639",
        "acq_date": "2025-01-01",
        "acq_time": "1200",
        "satellite": "Terra",
        "instrument": "MODIS",
        "frp": "12.5",
        "confidence": "nominal",
    }


class FakeProvider:
    def __init__(self, observations=None, report=None):
        self.observations = observations or []
        self.report = report or {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def fetch_historical_data(self, **kwargs):
        self.fetch_kwargs = kwargs
        return self.observations

    def get_report(self):
        return self.report


class FakeClient:
    def __init__(self, rows=None, error=None):
        self.rows = rows or []
        self.error = error
        self.calls = []

    def fetch_area(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.rows

    def close(self):
        pass


def test_get_area_global_and_bounding_box():
    assert firms_adapter._get_area(None) == "world"
    assert firms_adapter._get_area(
        (68.0, 6.0, 98.0, 37.0)
    ) == "68.0,6.0,98.0,37.0"


def test_requested_sources_for_modis_only():
    sources = firms_adapter._get_requested_sources(
        START, END, ["MODIS"]
    )

    assert "MODIS_SP" in sources
    assert all("VIIRS" not in source for source in sources)
    assert all(not source.endswith("_NRT") for source in sources)


def test_requested_sources_for_viirs_only():
    sources = firms_adapter._get_requested_sources(
        START, END, ["VIIRS"]
    )

    assert sources
    assert all("VIIRS" in source for source in sources)

    selected = HistoricalFireDataProvider._select_sources(
        START, END, sources
    )

    assert selected
    assert all(source.endswith("_SP") for source in selected)

def test_rejects_unsupported_sensor():
    with pytest.raises(ValueError):
        firms_adapter._get_requested_sources(
            START, END, ["UNKNOWN"]
        )


def test_mock_mode_is_default(monkeypatch):
    expected = {"records": [], "metadata": {"provider": "mock"}}

    monkeypatch.delenv("FIRE_ATLAS_DATA_PROVIDER", raising=False)
    monkeypatch.setattr(
        firms_adapter, "get_mock_fire_data",
        lambda **kwargs: expected
    )

    result = firms_adapter.get_active_fire_data(
        START, END
    )

    assert result == expected


def test_invalid_provider_mode_rejected(monkeypatch):
    monkeypatch.setenv("FIRE_ATLAS_DATA_PROVIDER", "invalid")

    with pytest.raises(ValueError):
        firms_adapter.get_active_fire_data(START, END)


def test_nasa_adapter_converts_observation(monkeypatch):
    fake = FakeProvider(
        observations=[make_observation()],
        report={
            "successful_requests": 1,
            "empty_requests": 0,
            "failed_requests": 0,
            "invalid_observations": 0,
            "selected_datasets": ["MODIS_SP"],
        },
    )

    monkeypatch.setattr(
        firms_adapter, "_get_requested_sources",
        lambda *args: ["MODIS_SP"]
    )
    monkeypatch.setattr(
        firms_adapter, "HistoricalFireDataProvider",
        lambda: fake
    )

    result = firms_adapter._get_nasa_data(
        START, END, None, ["MODIS"]
    )

    assert len(result["records"]) == 1
    record = result["records"][0]

    assert record["sensor"] == "MODIS"
    assert record["latitude"] == 22.5726
    assert record["longitude"] == 88.3639
    assert record["frp_mw"] == 12.5
    assert record["source_product"] == "MODIS_SP"
    assert record["is_synthetic"] is False
    assert record["source_attributes"]["source_dataset"] == "MODIS_SP"

    assert result["metadata"]["provider"] == "nasa_firms"
    assert result["metadata"]["data_status"] == "available"
    assert result["metadata"]["records_returned"] == 1


def test_nasa_adapter_empty_response(monkeypatch):
    fake = FakeProvider(
        observations=[],
        report={
            "successful_requests": 1,
            "empty_requests": 1,
            "failed_requests": 0,
            "invalid_observations": 0,
            "selected_datasets": ["MODIS_SP"],
        },
    )

    monkeypatch.setattr(
        firms_adapter, "_get_requested_sources",
        lambda *args: ["MODIS_SP"]
    )
    monkeypatch.setattr(
        firms_adapter, "HistoricalFireDataProvider",
        lambda: fake
    )

    result = firms_adapter._get_nasa_data(
        START, END, None, ["MODIS"]
    )

    assert result["records"] == []
    assert result["metadata"]["data_status"] == "no_matching_records"
    assert result["metadata"]["empty_requests"] == 1


def test_nasa_adapter_partial_failure(monkeypatch):
    fake = FakeProvider(
        observations=[make_observation()],
        report={
            "successful_requests": 1,
            "empty_requests": 0,
            "failed_requests": 1,
            "invalid_observations": 0,
            "selected_datasets": ["MODIS_SP"],
        },
    )

    monkeypatch.setattr(
        firms_adapter, "_get_requested_sources",
        lambda *args: ["MODIS_SP"]
    )
    monkeypatch.setattr(
        firms_adapter, "HistoricalFireDataProvider",
        lambda: fake
    )

    result = firms_adapter._get_nasa_data(
        START, END, None, ["MODIS"]
    )

    assert len(result["records"]) == 1
    assert result["metadata"]["data_status"] == "partial"
    assert result["metadata"]["failed_requests"] == 1


def test_nasa_adapter_total_failure(monkeypatch):
    fake = FakeProvider(
        observations=[],
        report={
            "successful_requests": 0,
            "empty_requests": 0,
            "failed_requests": 1,
            "invalid_observations": 0,
            "selected_datasets": ["MODIS_SP"],
        },
    )

    monkeypatch.setattr(
        firms_adapter, "_get_requested_sources",
        lambda *args: ["MODIS_SP"]
    )
    monkeypatch.setattr(
        firms_adapter, "HistoricalFireDataProvider",
        lambda: fake
    )

    result = firms_adapter._get_nasa_data(
        START, END, None, ["MODIS"]
    )

    assert result["records"] == []
    assert result["metadata"]["data_status"] == "unavailable"


def test_nasa_adapter_no_available_dataset(monkeypatch):
    monkeypatch.setattr(
        firms_adapter, "_get_requested_sources",
        lambda *args: []
    )

    result = firms_adapter._get_nasa_data(
        date(1990, 1, 1),
        date(1990, 1, 2),
        None,
        ["MODIS"],
    )

    assert result["records"] == []
    assert result["metadata"]["availability_status"] == "no_dataset_available"
    assert result["metadata"]["data_status"] == "no_matching_records"


def test_provider_successful_observation():
    client = FakeClient(rows=[make_firms_row()])
    provider = HistoricalFireDataProvider(client=client)

    observations = provider.fetch_historical_data(
        area="world",
        start_date=START,
        end_date=END,
        sources=["MODIS_SP"],
    )

    report = provider.get_report()

    assert len(observations) == 1
    assert observations[0].instrument == "MODIS"
    assert observations[0].frp == 12.5
    assert report["successful_requests"] == 1
    assert report["failed_requests"] == 0
    assert report["invalid_observations"] == 0
    assert client.calls[0]["source"] == "MODIS_SP"


def test_provider_empty_response():
    client = FakeClient(rows=[])
    provider = HistoricalFireDataProvider(client=client)

    observations = provider.fetch_historical_data(
        area="world",
        start_date=START,
        end_date=END,
        sources=["MODIS_SP"],
    )

    report = provider.get_report()

    assert observations == []
    assert report["successful_requests"] == 1
    assert report["empty_requests"] == 1
    assert report["failed_requests"] == 0


def test_provider_invalid_observation_is_counted():
    invalid_row = make_firms_row()
    invalid_row["latitude"] = "999"

    client = FakeClient(rows=[invalid_row])
    provider = HistoricalFireDataProvider(client=client)

    observations = provider.fetch_historical_data(
        area="world",
        start_date=START,
        end_date=END,
        sources=["MODIS_SP"],
    )

    report = provider.get_report()

    assert observations == []
    assert report["invalid_observations"] == 1
    assert report["successful_requests"] == 1


def test_provider_request_failure_is_counted():
    client = FakeClient(error=FirmsApiError("simulated failure"))
    provider = HistoricalFireDataProvider(client=client)

    observations = provider.fetch_historical_data(
        area="world",
        start_date=START,
        end_date=END,
        sources=["MODIS_SP"],
    )

    report = provider.get_report()

    assert observations == []
    assert report["failed_requests"] == 1
    assert report["successful_requests"] == 0
    assert report["selected_datasets"] == ["MODIS_SP"]


def test_provider_rejects_invalid_date_range():
    client = FakeClient()
    provider = HistoricalFireDataProvider(client=client)

    with pytest.raises(ValueError):
        provider.fetch_historical_data(
            area="world",
            start_date=date(2025, 1, 2),
            end_date=date(2025, 1, 1),
            sources=["MODIS_SP"],
        )


def test_provider_rejects_invalid_area():
    client = FakeClient()
    provider = HistoricalFireDataProvider(client=client)

    with pytest.raises(ValueError):
        provider.fetch_historical_data(
            area="invalid-area",
            start_date=START,
            end_date=END,
            sources=["MODIS_SP"],
        )
