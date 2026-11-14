from datetime import date

from app.ingestion.firms.provider import HistoricalFireDataProvider


class MockFirmsClient:
    """Mock NASA FIRMS client for testing without API requests."""

    def __init__(self):
        self.calls = []

    def fetch_area(self, source, area, day_range=1, date=None):
        """Return sample fire observations instead of calling NASA FIRMS."""

        self.calls.append({
            "source": source,
            "area": area,
            "day_range": day_range,
            "date": date,
        })

        return [
            {
                "latitude": "22.5726",
                "longitude": "88.3639",
                "acq_date": "2026-08-01",
                "acq_time": "1030",
                "satellite": "A",
                "instrument": "MODIS",
                "source_dataset": source,
                "brightness": "320.5",
                "bright_t31": "290.2",
                "scan": "1.0",
                "track": "1.0",
                "confidence": "85",
                "frp": "12.5",
                "daynight": "D",
                "version": "6.1",
            }
        ]


def test_date_window_generation():

    print("\nTesting five-day date windows...")

    mock_client = MockFirmsClient()

    provider = HistoricalFireDataProvider(
        client=mock_client
    )

    windows = list(
        provider._generate_date_windows(
            date(2026, 8, 1),
            date(2026, 8, 12)
        )
    )

    assert len(windows) == 3

    assert windows[0] == (
        date(2026, 8, 1), 5
    )

    assert windows[1] == (
        date(2026, 8, 6), 5
    )

    assert windows[2] == (
        date(2026, 8, 11), 2
    )

    print("PASS: Five-day splitting works.")

def test_dataset_selection():
    """Check that the correct dataset is selected for a date range."""

    print("\nTesting dataset selection...")

    selected = HistoricalFireDataProvider._select_sources(
        date(2026, 8, 1),
        date(2026, 8, 10),
        ["MODIS_SP", "MODIS_NRT"],
    )

    assert "MODIS_SP" in selected, (
        "MODIS_SP should be selected for August 2026."
    )

    assert "MODIS_NRT" not in selected, (
        "MODIS_NRT should not be selected because its availability "
        "starts in September 2026."
    )

    print("PASS: Dataset selection works.")


def test_historical_retrieval():
    """Check historical data retrieval using a mock FIRMS client."""

    print("\nTesting historical fire data retrieval...")

    mock_client = MockFirmsClient()
    provider = HistoricalFireDataProvider(client=mock_client)

    observations = provider.fetch_historical_data(
        area="87,21,89,23",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 7),
        sources=["MODIS_SP"],
    )

    # The requested period should produce two API calls:
    # August 1–5 and August 6–7.
    assert len(mock_client.calls) == 2, (
        f"Expected 2 API calls, got {len(mock_client.calls)}"
    )

    # Both mock calls return the same observation.
    # The provider should remove the duplicate.
    assert len(observations) == 1, (
        f"Expected 1 unique observation, got {len(observations)}"
    )

    assert observations[0].latitude == 22.5726
    assert observations[0].longitude == 88.3639

    report = provider.get_report()

    assert report["failed_requests"] == 0, (
        "There should be no failed requests."
    )

    provider.close()

    print("PASS: Historical data retrieval works.")
    print(f"Retrieved observations: {len(observations)}")
    print(f"Mock API calls: {len(mock_client.calls)}")


if __name__ == "__main__":
    print("=" * 50)
    print("NASA FIRMS PROVIDER TESTS")
    print("=" * 50)

    test_date_window_generation()
    test_dataset_selection()
    test_historical_retrieval()

    print("\n" + "=" * 50)
    print("ALL PROVIDER TESTS COMPLETED SUCCESSFULLY")
    print("=" * 50)
