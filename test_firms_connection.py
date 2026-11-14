from backend.app.ingestion.firms.client import (
    FirmsClient,
    FirmsApiError
)


def main():

    print("Connecting to NASA FIRMS...")

    sources = [
        "MODIS_NRT",
        "VIIRS_SNPP_NRT",
        "VIIRS_NOAA20_NRT",
        "VIIRS_NOAA21_NRT"
    ]

    try:

        with FirmsClient() as client:

            for source in sources:

                print(f"\nTesting {source}...")

                observations = client.fetch_area(
                    source=source,
                    area="68,6,98,37",
                    day_range=5
                )

                print(
                    f"Retrieved observations: "
                    f"{len(observations)}"
                )

                if observations:

                    print(
                        "Available columns:",
                        list(observations[0].keys())
                    )

                else:

                    print("No observations returned.")

    except (FirmsApiError, ValueError) as error:

        print("\nFIRMS connection failed:")
        print(error)


if __name__ == "__main__":
    main()