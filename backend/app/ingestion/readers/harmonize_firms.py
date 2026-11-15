
"""
FIRE ATLAS — MODIS / VIIRS data harmonization

Purpose:
1. Read normalized FIRMS CSVs (Asia / North America).
2. Read raw FIRMS CSVs (Europe).
3. Convert both formats into a common observation schema.
4. Preserve original source values and metadata.
5. Generate a daily sensor-wise detection summary.
6. Write invalid records to a separate rejection file.

This performs schema harmonization, NOT scientific sensor calibration.
"""

import argparse
import csv
import json
import math
from collections import Counter
from datetime import date
from pathlib import Path


OUTPUT_FIELDS = [
    "latitude",
    "longitude",
    "acquisition_date",
    "acquisition_time",
    "sensor",
    "satellite",
    "instrument",
    "source_dataset",
    "product_version",
    "brightness",
    "bright_t31",
    "bright_ti4",
    "bright_ti5",
    "scan",
    "track",
    "confidence_raw",
    "frp",
    "daynight",
    "raw_properties",
]


def first_value(row, *keys):
    """Return the first non-empty value from candidate columns."""
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return None


def parse_float(value, field_name="value", required=False):
    if value is None or str(value).strip() == "":
        if required:
            raise ValueError(f"Missing {field_name}")
        return None

    number = float(value)

    if not math.isfinite(number):
        raise ValueError(f"Invalid {field_name}: {value}")

    return number


def parse_date(value):
    if not value:
        raise ValueError("Missing acquisition date")

    # Supports YYYY-MM-DD and common FIRMS date format YYYY-MM-DD.
    return date.fromisoformat(str(value).strip()).isoformat()


def normalize_time(value):
    """
    Normalize FIRMS HHMM time into HH:MM.

    Examples:
        0     -> 00:00
        224   -> 02:24
        1106  -> 11:06

    No timezone conversion is performed.
    """
    if value is None or str(value).strip() == "":
        return None

    raw = str(value).strip()

    if ":" in raw:
        parts = raw.split(":")
        if len(parts) not in (2, 3):
            raise ValueError(f"Invalid time: {raw}")

        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) == 3 else 0
    else:
        digits = raw.zfill(4)

        if not digits.isdigit() or len(digits) != 4:
            raise ValueError(f"Invalid FIRMS time: {raw}")

        hour = int(digits[:2])
        minute = int(digits[2:])
        second = 0

    if not (0 <= hour <= 23 and 0 <= minute <= 59
            and 0 <= second <= 59):
        raise ValueError(f"Out-of-range time: {raw}")

    return f"{hour:02d}:{minute:02d}"


def identify_sensor(instrument, satellite, source_dataset):
    """
    Identify sensor from source metadata.
    Do not infer a sensor from geographic location.
    """
    instrument = (instrument or "").upper()
    satellite = (satellite or "").upper()
    dataset = (source_dataset or "").upper()

    if "MODIS" in instrument or "MODIS" in dataset:
        return "MODIS"

    if "VIIRS" in instrument or "VIIRS" in dataset:
        return "VIIRS"

    # Satellite aliases are used only as a fallback.
    if satellite in {"TERRA", "AQUA"}:
        return "MODIS"

    if satellite in {"N", "NPP", "NOAA20", "NOAA21",
                     "NOAA-20", "NOAA-21"}:
        return "VIIRS"

    raise ValueError(
        f"Cannot identify sensor: instrument={instrument}, "
        f"satellite={satellite}, dataset={dataset}"
    )


def harmonize_row(row, fallback_source_dataset=None):
    """Convert one raw or normalized FIRMS row to common schema."""

    # Supports both normalized and original FIRMS column names.
    latitude = parse_float(
        first_value(row, "latitude"), "latitude", required=True
    )
    longitude = parse_float(
        first_value(row, "longitude"), "longitude", required=True
    )

    if not -90 <= latitude <= 90:
        raise ValueError(f"Latitude out of range: {latitude}")

    if not -180 <= longitude <= 180:
        raise ValueError(f"Longitude out of range: {longitude}")

    acquisition_date = parse_date(
        first_value(row, "acquisition_date", "acq_date")
    )

    acquisition_time = normalize_time(
        first_value(row, "acquisition_time", "acq_time")
    )

    satellite = first_value(row, "satellite")
    instrument = first_value(row, "instrument")

    source_dataset = (
        first_value(row, "source_dataset")
        or fallback_source_dataset
    )

    if not source_dataset:
        raise ValueError(
            "Missing source_dataset. Supply a verified dataset "
            "identifier; do not invent one."
        )

    sensor = identify_sensor(
        instrument, satellite, source_dataset
    )

    frp = parse_float(
        first_value(row, "frp"), "frp"
    )

    if frp is not None and frp < 0:
        raise ValueError(f"Negative FRP: {frp}")

    # Preserve the original confidence representation.
    confidence = first_value(row, "confidence")

    # Preserve the complete original row, including sensor-specific fields.
    raw_properties = json.dumps(
        row, ensure_ascii=False, sort_keys=True
    )

    return {
        "latitude": latitude,
        "longitude": longitude,
        "acquisition_date": acquisition_date,
        "acquisition_time": acquisition_time,
        "sensor": sensor,
        "satellite": satellite,
        "instrument": instrument,
        "source_dataset": source_dataset,
        "product_version": first_value(row, "version"),
        "brightness": parse_float(
            first_value(row, "brightness")
        ),
        "bright_t31": parse_float(
            first_value(row, "bright_t31")
        ),
        "bright_ti4": parse_float(
            first_value(row, "bright_ti4")
        ),
        "bright_ti5": parse_float(
            first_value(row, "bright_ti5")
        ),
        "scan": parse_float(first_value(row, "scan")),
        "track": parse_float(first_value(row, "track")),
        "confidence_raw": confidence,
        "frp": frp,
        "daynight": first_value(row, "daynight"),
        "raw_properties": raw_properties,
    }


def process_file(
    input_path,
    output_writer,
    reject_writer,
    daily_counts,
    fallback_source_dataset=None,
):
    total = 0
    accepted = 0
    rejected = 0

    with input_path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as source:
        reader = csv.DictReader(source)

        if not reader.fieldnames:
            raise ValueError(f"No CSV headers found: {input_path}")

        for line_number, row in enumerate(reader, start=2):
            total += 1

            try:
                record = harmonize_row(
                    row,
                    fallback_source_dataset=fallback_source_dataset,
                )

                output_writer.writerow(record)

                daily_counts[
                    (record["acquisition_date"], record["sensor"])
                ] += 1

                accepted += 1

            except Exception as exc:
                reject_writer.writerow({
                    "source_file": str(input_path),
                    "line_number": line_number,
                    "error": str(exc),
                    "raw_row": json.dumps(
                        row, ensure_ascii=False
                    ),
                })
                rejected += 1

    return total, accepted, rejected


def main():
    parser = argparse.ArgumentParser(
        description="FIRE ATLAS MODIS/VIIRS harmonization"
    )

    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="CSV files or directories containing CSV files",
    )

    parser.add_argument(
        "--output",
        default="data/harmonized/fire_observations.csv",
    )

    parser.add_argument(
        "--source-dataset",
        default=None,
        help=(
            "Verified fallback dataset identifier for files "
            "without a source_dataset column"
        ),
    )

    args = parser.parse_args()

    input_files = []

    for item in args.input:
        path = Path(item)

        if path.is_file() and path.suffix.lower() == ".csv":
            input_files.append(path)

        elif path.is_dir():
            input_files.extend(sorted(path.rglob("*.csv")))

        else:
            print(f"WARNING: Input not found or not a CSV: {path}")

    input_files = sorted(set(input_files))

    if not input_files:
        raise SystemExit("No input CSV files found.")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    reject_path = output_path.with_name(
        output_path.stem + "_rejected.csv"
    )

    summary_path = output_path.with_name(
        output_path.stem + "_daily_summary.csv"
    )

    daily_counts = Counter()

    totals = accepted_total = rejected_total = 0

    with (
        output_path.open(
            "w", encoding="utf-8", newline=""
        ) as output_file,
        reject_path.open(
            "w", encoding="utf-8", newline=""
        ) as reject_file,
    ):
        output_writer = csv.DictWriter(
            output_file, fieldnames=OUTPUT_FIELDS
        )
        output_writer.writeheader()

        reject_fields = [
            "source_file", "line_number", "error", "raw_row"
        ]
        reject_writer = csv.DictWriter(
            reject_file, fieldnames=reject_fields
        )
        reject_writer.writeheader()

        for input_path in input_files:
            print(f"Processing: {input_path}")

            total, accepted, rejected = process_file(
                input_path,
                output_writer,
                reject_writer,
                daily_counts,
                args.source_dataset,
            )

            totals += total
            accepted_total += accepted
            rejected_total += rejected

            print(
                f"  Rows: {total:,} | "
                f"Accepted: {accepted:,} | "
                f"Rejected: {rejected:,}"
            )

    with summary_path.open(
        "w", encoding="utf-8", newline=""
    ) as summary_file:
        writer = csv.DictWriter(
            summary_file,
            fieldnames=[
                "acquisition_date",
                "sensor",
                "detection_count",
            ],
        )
        writer.writeheader()

        for (day, sensor), count in sorted(daily_counts.items()):
            writer.writerow({
                "acquisition_date": day,
                "sensor": sensor,
                "detection_count": count,
            })

    print("\n========== HARMONIZATION COMPLETE ==========")
    print(f"Input files:       {len(input_files)}")
    print(f"Total rows:        {totals:,}")
    print(f"Accepted rows:     {accepted_total:,}")
    print(f"Rejected rows:     {rejected_total:,}")
    print(f"Unified data:      {output_path}")
    print(f"Rejected records:  {reject_path}")
    print(f"Daily summary:     {summary_path}")


if __name__ == "__main__":
    main()
