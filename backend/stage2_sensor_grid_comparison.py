import csv
from collections import defaultdict

INPUT_FILE = r".\india_january_2025_grid_1km_exploratory.csv"
OUTPUT_FILE = r".\india_january_2025_sensor_grid_comparison.csv"

cells = defaultdict(lambda: {
    "MODIS": 0,
    "VIIRS": 0,
    "MODIS_FRP": 0.0,
    "VIIRS_FRP": 0.0
})

with open(INPUT_FILE, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        key = (
            row["date"],
            row["grid_x"],
            row["grid_y"]
        )

        sensor = row["sensor"]
        count = int(row["detection_records"])
        frp = float(row["frp_sum_mw"])

        cells[key][sensor] += count
        cells[key][sensor + "_FRP"] += frp

shared = 0
modis_only = 0
viirs_only = 0
both_zero = 0
ratios = []

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    fields = [
        "date", "grid_x", "grid_y",
        "modis_detections", "viirs_detections",
        "viirs_modis_ratio",
        "modis_frp_sum_mw", "viirs_frp_sum_mw",
        "sensor_presence"
    ]

    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    for key, item in sorted(cells.items()):
        m = item["MODIS"]
        v = item["VIIRS"]

        if m > 0 and v > 0:
            presence = "BOTH"
            shared += 1
            ratios.append(v / m)
        elif m > 0:
            presence = "MODIS_ONLY"
            modis_only += 1
        elif v > 0:
            presence = "VIIRS_ONLY"
            viirs_only += 1
        else:
            presence = "NEITHER"
            both_zero += 1

        writer.writerow({
            "date": key[0],
            "grid_x": key[1],
            "grid_y": key[2],
            "modis_detections": m,
            "viirs_detections": v,
            "viirs_modis_ratio": round(v / m, 4) if m else "",
            "modis_frp_sum_mw": round(item["MODIS_FRP"], 3),
            "viirs_frp_sum_mw": round(item["VIIRS_FRP"], 3),
            "sensor_presence": presence
        })

print("GRID-DAY COMPARISON COMPLETE")
print("Total observed grid-days:", len(cells))
print("Shared MODIS + VIIRS grid-days:", shared)
print("MODIS-only grid-days:", modis_only)
print("VIIRS-only grid-days:", viirs_only)
print("Neither:", both_zero)

if ratios:
    print("Mean ratio in shared grid-days:", round(sum(ratios)/len(ratios), 3))
    print("Median ratio in shared grid-days:", round(sorted(ratios)[len(ratios)//2], 3))

print("Output:", OUTPUT_FILE)
