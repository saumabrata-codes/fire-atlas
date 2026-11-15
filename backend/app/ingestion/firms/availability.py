import csv
import io
import logging
from datetime import date
from typing import Optional

import requests

from .config import get_firms_api_key


logger = logging.getLogger(__name__)


class DatasetAvailability:
    """
    Manage NASA FIRMS availability using an explicit dynamic refresh.

    DATASETS is the static fallback snapshot recorded on November 12,
    2026. A successful refresh replaces the active snapshot in memory,
    without modifying the fallback.

    Availability does not guarantee observations for every date.

    Active availability is shared within this Python process.
    Lookup methods never make network requests.
    """

    AVAILABILITY_URL = (
        "https://firms.modaps.eosdis.nasa.gov/"
        "api/data_availability/csv"
    )

    DATASETS = {
        "MODIS_SP": {
            "first_available": date(2000, 11, 1),
            "last_available": date(2026, 8, 31),
            "satellite": "MODIS",
            "processing": "SP",
        },
        "MODIS_NRT": {
            "first_available": date(2026, 9, 1),
            "last_available": date(2026, 11, 12),
            "satellite": "MODIS",
            "processing": "NRT",
        },
        "VIIRS_SNPP_SP": {
            "first_available": date(2012, 1, 20),
            "last_available": date(2026, 7, 31),
            "satellite": "VIIRS_SNPP",
            "processing": "SP",
        },
        "VIIRS_SNPP_NRT": {
            "first_available": date(2026, 8, 1),
            "last_available": date(2026, 11, 2),
            "satellite": "VIIRS_SNPP",
            "processing": "NRT",
        },
        "VIIRS_NOAA20_SP": {
            "first_available": date(2018, 4, 1),
            "last_available": date(2026, 7, 31),
            "satellite": "VIIRS_NOAA20",
            "processing": "SP",
        },
        "VIIRS_NOAA20_NRT": {
            "first_available": date(2026, 8, 1),
            "last_available": date(2026, 11, 12),
            "satellite": "VIIRS_NOAA20",
            "processing": "NRT",
        },
        "VIIRS_NOAA21_SP": {
            "first_available": date(2023, 3, 1),
            "last_available": date(2026, 7, 31),
            "satellite": "VIIRS_NOAA21",
            "processing": "SP",
        },
        "VIIRS_NOAA21_NRT": {
            "first_available": date(2024, 1, 17),
            "last_available": date(2026, 11, 12),
            "satellite": "VIIRS_NOAA21",
            "processing": "NRT",
        },
    }

    _active_datasets: Optional[dict] = None

    @classmethod
    def _current_datasets(cls) -> dict:
        """Return the active snapshot or the static fallback."""
        if cls._active_datasets is not None:
            return cls._active_datasets
        return cls.DATASETS

    @staticmethod
    def _parse_date(value: Optional[str]) -> date:
        """Require a canonical YYYY-MM-DD date."""
        if not isinstance(value, str):
            raise ValueError("Missing availability date.")

        value = value.strip()
        parsed = date.fromisoformat(value)

        if parsed.isoformat() != value:
            raise ValueError("Invalid availability date format.")

        return parsed

    @classmethod
    def _parse_availability_csv(cls, text: str) -> dict:
        """
        Validate a complete snapshot before it becomes active.

        Unknown products are ignored. Every supported product must
        appear exactly once with a valid, non-reversed date range.
        """
        reader = csv.DictReader(
            io.StringIO(text.lstrip("\ufeff")),
            strict=True,
        )

        headers = reader.fieldnames
        required_headers = {"data_id", "min_date", "max_date"}

        if (
            not headers
            or len(headers) != len(set(headers))
            or not required_headers.issubset(headers)
        ):
            raise ValueError("Invalid availability CSV headers.")

        parsed = {}

        for row in reader:
            source = (row.get("data_id") or "").strip()

            if source not in cls.DATASETS:
                continue

            if source in parsed:
                raise ValueError("Duplicate supported dataset.")

            if None in row:
                raise ValueError("Malformed availability CSV row.")

            first_available = cls._parse_date(row.get("min_date"))
            last_available = cls._parse_date(row.get("max_date"))

            if first_available > last_available:
                raise ValueError("Reversed availability date range.")

            info = cls.DATASETS[source].copy()
            info["first_available"] = first_available
            info["last_available"] = last_available
            parsed[source] = info

        if set(parsed) != set(cls.DATASETS):
            raise ValueError("Incomplete supported dataset availability.")

        # Preserve the existing dataset order.
        return {
            source: parsed[source]
            for source in cls.DATASETS
        }

    @classmethod
    def refresh_from_nasa(
        cls,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ) -> bool:
        """
        Explicitly retrieve and activate NASA availability metadata.

        Return True only after validating all supported datasets.
        On configuration, request, or response-validation failure,
        return False and retain the previous snapshot.

        Invalid explicit arguments raise ValueError.
        Request URLs and raw errors are never logged.
        """
        if (
            not isinstance(timeout, int)
            or isinstance(timeout, bool)
            or timeout <= 0
        ):
            raise ValueError("timeout must be a positive integer.")

        if api_key is not None:
            if not isinstance(api_key, str) or not api_key.strip():
                raise ValueError("api_key must be a nonempty string.")
            key = api_key.strip()
        else:
            try:
                key = get_firms_api_key()
            except ValueError:
                logger.warning(
                    "FIRMS availability refresh skipped: "
                    "API key configuration is missing."
                )
                return False

        url = f"{cls.AVAILABILITY_URL}/{key}/ALL"

        try:
            with requests.get(url, timeout=timeout) as response:
                response.raise_for_status()
                updated = cls._parse_availability_csv(response.text)

        except requests.RequestException:
            logger.warning(
                "FIRMS availability refresh failed: "
                "request error; previous snapshot retained."
            )
            return False

        except (ValueError, csv.Error):
            logger.warning(
                "FIRMS availability refresh failed: "
                "invalid response; previous snapshot retained."
            )
            return False

        # Do not alter active state until the entire response is valid.
        cls._active_datasets = updated
        return True

    @classmethod
    def get_dataset_info(cls, source: str) -> dict:
        """Return availability information for a dataset."""
        datasets = cls._current_datasets()

        if source not in datasets:
            raise ValueError(f"Unknown FIRMS dataset: {source}")

        return datasets[source].copy()

    @classmethod
    def is_date_available(
        cls,
        source: str,
        target_date: date,
    ) -> bool:
        """Check whether a dataset covers a specific date."""
        info = cls.get_dataset_info(source)

        return (
            info["first_available"]
            <= target_date
            <= info["last_available"]
        )

    @classmethod
    def get_available_sources(
        cls,
        start_date: date,
        end_date: date,
    ) -> list[str]:
        """Return datasets overlapping the requested date range."""
        if start_date > end_date:
            raise ValueError("start_date cannot be after end_date.")

        return [
            source
            for source, info in cls._current_datasets().items()
            if (
                start_date <= info["last_available"]
                and end_date >= info["first_available"]
            )
        ]

    @classmethod
    def get_all_datasets(cls) -> dict:
        """Return copies of all active dataset records."""
        return {
            source: info.copy()
            for source, info in cls._current_datasets().items()
        }
