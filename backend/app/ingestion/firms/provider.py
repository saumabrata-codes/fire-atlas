from datetime import date, datetime, timedelta
from typing import Optional

from .client import FirmsClient, FirmsApiError
from .availability import DatasetAvailability
from .models import (
    FireObservation,
    ObservationValidationError
)


class HistoricalFireDataProvider:
    """
    Retrieves and standardizes historical fire observations
    from NASA FIRMS MODIS and VIIRS datasets.
    """

    MAX_DAY_RANGE = 5

    def __init__(
        self,
        client: Optional[FirmsClient] = None
    ):
        self.client = client or FirmsClient()
        self._owns_client = client is None

        self.report = {
            "successful_requests": 0,
            "empty_requests": 0,
            "failed_requests": 0,
            "invalid_observations": 0,
            "errors": []
        }

    @staticmethod
    def _validate_dates(
        start_date: date,
        end_date: date
    ):
        # datetime is a subclass of date, so reject it explicitly.
        # This provider works with calendar dates only.
        if not isinstance(start_date, date) or isinstance(
            start_date, datetime
        ):
            raise ValueError(
                "Invalid start_date. Expected a date, not datetime."
            )

        if not isinstance(end_date, date) or isinstance(
            end_date, datetime
        ):
            raise ValueError(
                "Invalid end_date. Expected a date, not datetime."
            )

        if start_date > end_date:
            raise ValueError(
                "start_date cannot be after end_date."
            )

    @staticmethod
    def _validate_area(area: str):
        FirmsClient._validate_area(area)

    @staticmethod
    def _select_sources(
        start_date: date,
        end_date: date,
        requested_sources: Optional[list[str]] = None
    ) -> dict[str, tuple[date, date]]:
        """
        Select available datasets and avoid overlapping
        Standard Processing and Near Real-Time products
        for the same satellite.

        Standard Processing is preferred when available.
        """

        all_datasets = DatasetAvailability.get_all_datasets()

        if requested_sources is None:
            candidates = list(all_datasets.keys())
        else:
            candidates = list(dict.fromkeys(requested_sources))

            unknown = [
                source for source in candidates
                if source not in all_datasets
            ]

            if unknown:
                raise ValueError(
                    f"Unknown datasets: {unknown}"
                )

        selected = {}

        for source in candidates:

            info = all_datasets[source]

            dataset_start = max(
                start_date,
                info["first_available"]
            )

            dataset_end = min(
                end_date,
                info["last_available"]
            )

            if dataset_start > dataset_end:
                continue

            # Avoid fetching overlapping NRT dates
            # when Standard Processing is available.
            if info["processing"] == "NRT":

                standard_sources = [
                    name
                    for name, standard_info
                    in all_datasets.items()
                    if (
                        standard_info["satellite"]
                        == info["satellite"]
                        and standard_info["processing"] == "SP"
                    )
                ]

                for standard_source in standard_sources:

                    standard_info = all_datasets[
                        standard_source
                    ]

                    dataset_start = max(
                        dataset_start,
                        standard_info["last_available"]
                        + timedelta(days=1)
                    )

            if dataset_start <= dataset_end:
                selected[source] = (
                    dataset_start,
                    dataset_end
                )

        return selected

    def _generate_date_windows(
        self,
        start_date: date,
        end_date: date
    ):
        """
        Generate consecutive date windows of maximum
        five days each.
        """

        current_date = start_date

        while current_date <= end_date:

            window_end = min(
                current_date + timedelta(
                    days=self.MAX_DAY_RANGE - 1
                ),
                end_date
            )

            day_range = (
                window_end - current_date
            ).days + 1

            yield current_date, day_range

            current_date = (
                window_end + timedelta(days=1)
            )

    @staticmethod
    def _observation_key(
        observation: FireObservation
    ):
        """
        Identify duplicate observations across datasets.
        """

        return (
            observation.latitude,
            observation.longitude,
            observation.acquisition_date,
            observation.acquisition_time,
            observation.satellite,
            observation.instrument
        )

    def fetch_historical_data(
        self,
        area: str,
        start_date: date,
        end_date: date,
        sources: Optional[list[str]] = None
    ) -> list[FireObservation]:
        """
        Retrieve historical observations.

        Args:
            area:
                Geographic bounding box or world.

            start_date:
                Historical start date.

            end_date:
                Historical end date.

            sources:
                Optional list of FIRMS datasets.

        Returns:
            Deduplicated FireObservation objects.
        """

        self._validate_dates(start_date, end_date)
        self._validate_area(area)

        # Reset report for each retrieval.
        self.report = {
            "successful_requests": 0,
            "empty_requests": 0,
            "failed_requests": 0,
            "invalid_observations": 0,
            "errors": []
        }

        selected_sources = self._select_sources(
            start_date,
            end_date,
            sources
        )

        if not selected_sources:
            raise ValueError(
                "No FIRMS datasets are available "
                "for the requested date range."
            )

        observations = {}
        observation_errors = 0

        for source, date_range in selected_sources.items():

            source_start, source_end = date_range

            print(
                f"\nProcessing {source}: "
                f"{source_start} to {source_end}"
            )

            windows = self._generate_date_windows(
                source_start,
                source_end
            )

            for window_start, day_range in windows:

                print(
                    f"Fetching {source}: "
                    f"{window_start} "
                    f"({day_range} days)"
                )

                try:

                    rows = self.client.fetch_area(
                        source=source,
                        area=area,
                        day_range=day_range,
                        date=window_start.isoformat()
                    )

                    self.report["successful_requests"] += 1

                    if not rows:
                        self.report["empty_requests"] += 1
                        continue

                    for row in rows:

                        try:

                            observation = (
                                FireObservation.from_firms_row(
                                    row,
                                    source_dataset=source
                                )
                            )

                            key = self._observation_key(
                                observation
                            )

                            if key not in observations:
                                observations[key] = observation

                        except ObservationValidationError as error:

                            observation_errors += 1

                            self.report[
                                "invalid_observations"
                            ] += 1

                            self.report["errors"].append(
                                {
                                    "source": source,
                                    "error": str(error)
                                }
                            )

                except FirmsApiError as error:

                    self.report["failed_requests"] += 1

                    self.report["errors"].append(
                        {
                            "source": source,
                            "date": window_start.isoformat(),
                            "error": str(error)
                        }
                    )

                    print(f"Request failed: {error}")

        result = sorted(
            observations.values(),
            key=lambda item: (
                item.acquisition_date,
                item.acquisition_time or ""
            )
        )

        print("\nHistorical retrieval completed.")

        print(
            f"Total observations: {len(result)}"
        )

        print(
            f"Successful requests: "
            f"{self.report['successful_requests']}"
        )

        print(
            f"Empty requests: "
            f"{self.report['empty_requests']}"
        )

        print(
            f"Failed requests: "
            f"{self.report['failed_requests']}"
        )

        print(
            f"Invalid observations: "
            f"{observation_errors}"
        )

        return result

    def get_report(self) -> dict:
        """Return retrieval statistics."""

        return {
            **self.report,
            "errors": self.report["errors"].copy()
        }

    def close(self):
        """Close the client if this provider created it."""

        if self._owns_client:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ):
        self.close()