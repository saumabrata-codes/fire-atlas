from datetime import date

from backend.app.ingestion.firms.availability import (
    DatasetAvailability
)


def main():

    print("Testing FIRMS Dataset Availability\n")

    # Test 1: Historical date
    sources = DatasetAvailability.get_available_sources(
        date(2015, 1, 1),
        date(2015, 12, 31)
    )

    print("Available datasets for 2015:")
    for source in sources:
        print("-", source)

    # Test 2: Recent historical date
    sources = DatasetAvailability.get_available_sources(
        date(2025, 1, 1),
        date(2025, 12, 31)
    )

    print("\nAvailable datasets for 2025:")
    for source in sources:
        print("-", source)

    # Test 3: Current date
    sources = DatasetAvailability.get_available_sources(
        date(2026, 11, 12),
        date(2026, 11, 12)
    )

    print("\nAvailable datasets for 2026-11-12:")
    for source in sources:
        print("-", source)

    # Test 4: Specific dataset
    result = DatasetAvailability.is_date_available(
        "MODIS_SP",
        date(2010, 5, 10)
    )

    print("\nMODIS_SP available on 2010-05-10:", result)

    print("\nAll availability tests completed.")


if __name__ == "__main__":
    main()