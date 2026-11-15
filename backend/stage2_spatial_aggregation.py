import csv
from collections import defaultdict
from pyproj import Transformer

INPUT_FILE = r"..\india_firms_january_2025.csv"
OUTPUT_FILE = r".\india_january_2025_grid_1km_exploratory.csv"

GRID_SIZE_M = 1000

# WGS84 geographic coordinates -> global equal-area projected coordinates
forward = Transformer.from_crs(
    "EPSG:4326", "EPSG:6933", always_xy=True
)

# Projected grid-cell centres -> WGS84 for readable output coordinates
reverse = Transformer.from_crs(
    "EPSG:6933", "EPSG:4326", always_xy=True
)

aggregates = defaultdict(lambda: {
    "detection_records": 0,
    "frp_sum_mw": 0.0,
    "frp_values": [],
    "source_datasets": set()
})

input_rows = 0
skipped_rows = 0

with open(INPUT_FILE, newline="", encoding="utf-8-sig") as source:
    reader = csv.DictReader(source)

    for row in reader:
        try:
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            frp = float(row["frp"])

            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("Invalid coordinates")

            if frp < 0:
                raise ValueError("Negative FRP")

            x, y = forward.transform(lon, lat)

            grid_x = int(x // GRID_SIZE_M)
            grid_y = int(y // GRID_SIZE_M)

            key = (
                row["acquisition_date"],
                row["instrument"],
                row["satellite"],
                grid_x,
                grid_y
            )

            item = aggregates[key]
            item["detection_records"] += 1
            item["frp_sum_mw"] += frp
            item["frp_values"].append(frp)
            item["source_datasets"].add(row["source_dataset"])

            input_rows += 1

        except (ValueError, TypeError, KeyError):
            skipped_rows += 1

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as target:
    fieldnames = [
        "date",
        "sensor",
        "satellite",
        "grid_x",
        "grid_y",
        "grid_center_latitude",
        "grid_center_longitude",
        "detection_records",
        "frp_sum_mw",
        "frp_mean_mw",
        "frp_max_mw",
        "source_datasets"
    ]

    writer = csv.DictWriter(target, fieldnames=fieldnames)
    writer.writeheader()

    for key, item in sorted(aggregates.items()):
        date, sensor, satellite, grid_x, grid_y = key

        center_x = (grid_x + 0.5) * GRID_SIZE_M
        center_y = (grid_y + 0.5) * GRID_SIZE_M
        center_lon, center_lat = reverse.transform(center_x, center_y)

        values = item["frp_values"]
        count = item["detection_records"]

        writer.writerow({
            "date": date,
            "sensor": sensor,
            "satellite": satellite,
            "grid_x": grid_x,
            "grid_y": grid_y,
            "grid_center_latitude": round(center_lat, 6),
            "grid_center_longitude": round(center_lon, 6),
            "detection_records": count,
            "frp_sum_mw": round(item["frp_sum_mw"], 3),
            "frp_mean_mw": round(item["frp_sum_mw"] / count, 3),
            "frp_max_mw": round(max(values), 3),
            "source_datasets": ";".join(sorted(item["source_datasets"]))
        })

print("SPATIAL AGGREGATION COMPLETE")
print("Input rows processed:", input_rows)
print("Rows skipped:", skipped_rows)
print("Aggregated sensor-date-grid groups:", len(aggregates))
print("Grid resolution:", GRID_SIZE_M, "metres")
print("Projection: EPSG:6933")
print("Output:", OUTPUT_FILE)
