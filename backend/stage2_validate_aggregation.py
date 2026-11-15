import csv
from collections import Counter

path = r".\india_january_2025_grid_1km_exploratory.csv"

rows = 0
sensor_totals = Counter()
date_totals = Counter()
keys = Counter()
frp_errors = 0
invalid_counts = 0

with open(path, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        rows += 1

        sensor = row["sensor"]
        count = int(row["detection_records"])
        frp_sum = float(row["frp_sum_mw"])
        frp_mean = float(row["frp_mean_mw"])

        sensor_totals[sensor] += count
        date_totals[row["date"]] += count

        key = (
            row["date"], sensor, row["satellite"],
            row["grid_x"], row["grid_y"]
        )
        keys[key] += 1

        if count <= 0:
            invalid_counts += 1

        if abs(frp_sum - (frp_mean * count)) > max(0.01, frp_sum * 0.001):
            frp_errors += 1

print("AGGREGATED ROWS:", rows)
print("\nSENSOR DETECTION TOTALS")
for sensor, count in sensor_totals.items():
    print(sensor, count)

print("\nTOTAL DETECTIONS:", sum(sensor_totals.values()))
print("DATE COUNT:", len(date_totals))
print("FIRST DATE:", min(date_totals))
print("LAST DATE:", max(date_totals))

print("\nDUPLICATE AGGREGATION KEYS:", sum(v > 1 for v in keys.values()))
print("INVALID DETECTION COUNTS:", invalid_counts)
print("FRP CONSISTENCY WARNINGS:", frp_errors)

print("\nDAILY DETECTION TOTALS")
for date in sorted(date_totals):
    print(date, date_totals[date])
