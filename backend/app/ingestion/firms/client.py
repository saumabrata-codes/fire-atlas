
import csv
import io
import requests

from typing import Optional
from datetime import date as Date

from .config import get_firms_api_key


class FirmsApiError(Exception):
    """Raised when a NASA FIRMS API request fails."""


class FirmsClient:
    """
    NASA FIRMS API client.

    Supports all eight verified datasets:

    MODIS:
    - MODIS_SP
    - MODIS_NRT

    VIIRS Suomi-NPP:
    - VIIRS_SNPP_SP
    - VIIRS_SNPP_NRT

    VIIRS NOAA-20:
    - VIIRS_NOAA20_SP
    - VIIRS_NOAA20_NRT

    VIIRS NOAA-21:
    - VIIRS_NOAA21_SP
    - VIIRS_NOAA21_NRT
    """

    BASE_URL = (
        "https://firms.modaps.eosdis.nasa.gov/"
        "api/area/csv"
    )

    SUPPORTED_SOURCES = {
        # MODIS
        "MODIS_SP",
        "MODIS_NRT",

        # VIIRS Suomi-NPP
        "VIIRS_SNPP_SP",
        "VIIRS_SNPP_NRT",

        # VIIRS NOAA-20
        "VIIRS_NOAA20_SP",
        "VIIRS_NOAA20_NRT",

        # VIIRS NOAA-21
        "VIIRS_NOAA21_SP",
        "VIIRS_NOAA21_NRT",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        self.api_key = (
            api_key.strip()
            if api_key and api_key.strip()
            else get_firms_api_key()
        )

        if not self.api_key:
            raise ValueError(
                "NASA FIRMS API key is missing."
            )

        if (
            not isinstance(timeout, int)
            or isinstance(timeout, bool)
            or timeout <= 0
        ):
            raise ValueError(
                "timeout must be a positive integer."
            )

        self.timeout = timeout
        self.session = requests.Session()

    def fetch_area(
        self,
        source: str,
        area: str,
        day_range: int = 1,
        date: Optional[str] = None
    ) -> list[dict]:
        """
        Fetch active fire observations for a geographic area.

        Args:
            source:
                Supported NASA FIRMS dataset.

            area:
                Geographic bounding box:
                west,south,east,north
                or 'world'.

            day_range:
                Number of days (1-5).

            date:
                Optional historical date (YYYY-MM-DD).

        Returns:
            List of fire observation dictionaries.

        Raises:
            FirmsApiError:
                If the NASA FIRMS API request fails.

            ValueError:
                If request parameters are invalid.
        """

        # Validate source
        if source not in self.SUPPORTED_SOURCES:
            raise ValueError(
                f"Unsupported FIRMS source: {source}. "
                f"Supported sources: "
                f"{', '.join(sorted(self.SUPPORTED_SOURCES))}"
            )

        # Validate area
        self._validate_area(area)

        # Validate day range
        if (
            not isinstance(day_range, int)
            or isinstance(day_range, bool)
            or not 1 <= day_range <= 5
        ):
            raise ValueError(
                "day_range must be an integer between 1 and 5."
            )

        # Validate optional historical date
        if date is not None:

            if not isinstance(date, str):
                raise ValueError(
                    "date must use YYYY-MM-DD format."
                )

            try:
                parsed_date = Date.fromisoformat(date)

                if parsed_date.isoformat() != date:
                    raise ValueError

            except ValueError:
                raise ValueError(
                    "date must use YYYY-MM-DD format."
                )

        # Build API URL
        url = (
            f"{self.BASE_URL}/"
            f"{self.api_key}/"
            f"{source}/"
            f"{area}/"
            f"{day_range}"
        )

        # Append historical date when provided
        if date:
            url = f"{url}/{date}"

        try:

            response = self.session.get(
                url,
                timeout=self.timeout
            )

            response.raise_for_status()

            # Parse CSV response
            csv_data = csv.DictReader(
                io.StringIO(response.text)
            )

            observations = list(csv_data)

            return observations

        except requests.exceptions.Timeout as error:

            raise FirmsApiError(
                f"NASA FIRMS request timed out: {error}"
            ) from error

        except requests.exceptions.HTTPError as error:

            status_code = (
                error.response.status_code
                if error.response is not None
                else "Unknown"
            )

            response_text = (
                error.response.text[:500]
                if error.response is not None
                else ""
            )

            raise FirmsApiError(
                f"NASA FIRMS HTTP error "
                f"({status_code}): {response_text}"
            ) from error

        except requests.exceptions.ConnectionError as error:

            raise FirmsApiError(
                f"Could not connect to NASA FIRMS: {error}"
            ) from error

        except requests.exceptions.RequestException as error:

            raise FirmsApiError(
                f"NASA FIRMS request failed: {error}"
            ) from error

    @staticmethod
    def _validate_area(area: str) -> None:
        """Validate geographic bounding box."""

        if area == "world":
            return

        try:

            coordinates = [
                float(value)
                for value in area.split(",")
            ]

            if len(coordinates) != 4:
                raise ValueError

            west, south, east, north = coordinates

            if not (
                -180 <= west <= 180
                and -180 <= east <= 180
                and -90 <= south <= 90
                and -90 <= north <= 90
            ):
                raise ValueError

            if west >= east or south >= north:
                raise ValueError

        except (ValueError, AttributeError):
            raise ValueError(
                "Invalid area. Use "
                "'west,south,east,north' "
                "or 'world'."
            )

    def close(self):
        """Close the HTTP session."""

        self.session.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ):
        self.close()
