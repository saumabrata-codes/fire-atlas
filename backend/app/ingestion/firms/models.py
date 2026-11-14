
from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Any, Mapping
import math


class ObservationValidationError(ValueError):
    """Raised when a fire observation contains invalid data."""


@dataclass
class FireObservation:
    """Standardized MODIS and VIIRS fire observation."""

    latitude: float
    longitude: float

    acquisition_date: date
    acquisition_time: Optional[str]

    satellite: str
    instrument: str
    source_dataset: str

    # MODIS brightness fields
    brightness: Optional[float] = None
    bright_t31: Optional[float] = None

    # VIIRS brightness fields
    bright_ti4: Optional[float] = None
    bright_ti5: Optional[float] = None

    # Common fields
    scan: Optional[float] = None
    track: Optional[float] = None
    confidence: Optional[str] = None
    frp: Optional[float] = None
    daynight: Optional[str] = None
    version: Optional[str] = None

    raw_properties: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self):

        if not -90 <= self.latitude <= 90:
            raise ObservationValidationError(
                "Latitude must be between -90 and 90."
            )

        if not -180 <= self.longitude <= 180:
            raise ObservationValidationError(
                "Longitude must be between -180 and 180."
            )

        if not isinstance(self.acquisition_date, date):
            raise ObservationValidationError(
                "acquisition_date must be a date object."
            )

        if not self.source_dataset:
            raise ObservationValidationError(
                "source_dataset is required."
            )

        if not self.satellite:
            raise ObservationValidationError(
                "satellite is required."
            )

        if not self.instrument:
            raise ObservationValidationError(
                "instrument is required."
            )

    @staticmethod
    def _optional_float(
        value: Any,
        field_name: str
    ) -> Optional[float]:

        if value is None or str(value).strip() == "":
            return None

        try:
            result = float(value)

            if not math.isfinite(result):
                raise ValueError

            return result

        except (ValueError, TypeError):
            raise ObservationValidationError(
                f"Invalid numeric value for {field_name}: {value}"
            )

    @staticmethod
    def _optional_string(value: Any) -> Optional[str]:

        if value is None:
            return None

        result = str(value).strip()

        return result if result else None

    @classmethod
    def from_firms_row(
        cls,
        row: Mapping[str, Any],
        source_dataset: str
    ) -> "FireObservation":

        try:

            latitude = cls._optional_float(
                row.get("latitude"),
                "latitude"
            )

            longitude = cls._optional_float(
                row.get("longitude"),
                "longitude"
            )

            if latitude is None or longitude is None:
                raise ObservationValidationError(
                    "Latitude and longitude are required."
                )

            acquisition_date = date.fromisoformat(
                str(row["acq_date"]).strip()
            )

            return cls(
                latitude=latitude,
                longitude=longitude,

                acquisition_date=acquisition_date,

                acquisition_time=cls._optional_string(
                    row.get("acq_time")
                ),

                satellite=cls._optional_string(
                    row.get("satellite")
                ) or "UNKNOWN",

                instrument=cls._optional_string(
                    row.get("instrument")
                ) or "UNKNOWN",

                source_dataset=source_dataset,

                brightness=cls._optional_float(
                    row.get("brightness"),
                    "brightness"
                ),

                bright_t31=cls._optional_float(
                    row.get("bright_t31"),
                    "bright_t31"
                ),

                bright_ti4=cls._optional_float(
                    row.get("bright_ti4"),
                    "bright_ti4"
                ),

                bright_ti5=cls._optional_float(
                    row.get("bright_ti5"),
                    "bright_ti5"
                ),

                scan=cls._optional_float(
                    row.get("scan"),
                    "scan"
                ),

                track=cls._optional_float(
                    row.get("track"),
                    "track"
                ),

                confidence=cls._optional_string(
                    row.get("confidence")
                ),

                frp=cls._optional_float(
                    row.get("frp"),
                    "frp"
                ),

                daynight=cls._optional_string(
                    row.get("daynight")
                ),

                version=cls._optional_string(
                    row.get("version")
                ),

                raw_properties=dict(row)
            )

        except ObservationValidationError:
            raise

        except (ValueError, TypeError, KeyError) as error:
            raise ObservationValidationError(
                f"Could not convert FIRMS observation: {error}"
            ) from error

    def to_dict(self) -> dict[str, Any]:

        return {
            "latitude": self.latitude,
            "longitude": self.longitude,

            "acquisition_date": (
                self.acquisition_date.isoformat()
            ),

            "acquisition_time": self.acquisition_time,

            "satellite": self.satellite,
            "instrument": self.instrument,
            "source_dataset": self.source_dataset,

            "brightness": self.brightness,
            "bright_t31": self.bright_t31,
            "bright_ti4": self.bright_ti4,
            "bright_ti5": self.bright_ti5,

            "scan": self.scan,
            "track": self.track,

            "confidence": self.confidence,
            "frp": self.frp,
            "daynight": self.daynight,
            "version": self.version,

            "raw_properties": self.raw_properties
        }
