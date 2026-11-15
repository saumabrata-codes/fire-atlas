import csv
from collections import defaultdict, Counter
from statistics import median

path = r"..\india_firms_january_2025.csv"

daily = defaultdict(Counter)
frp = defaultdict(list)
confidence = defaultdict(Counter)

with open(path, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        day = row["acquisition_date"]
        sensor = row["instrument"]

        daily[day][sensor] += 1
        frp[sensor].append(float(row["frp"]))
        confidence[sensor][row["confidence"]] += 1

print("DATE       MODIS    VIIRS    TOTAL    VIIRS/MODIS")
print("-" * 58)

for day in sorted(daily):
    m = daily[day]["MODIS"]
    v = daily[day]["VIIRS"]
    ratio = round(v / m, 2) if m else "N/A"
    print(f"{day}   {m:6}   {v:6}   {m+v:6}   {ratio}")

print("\nSENSOR COVERAGE")
for sensor in ["MODIS", "VIIRS"]:
    active_days = sum(daily[d][sensor] > 0 for d in daily)
    print(sensor, "active days:", active_days, "/ 31")

print("\nFRP SUMMARY (MW)")
for sensor, values in frp.items():
    print(sensor, "count:", len(values),
          "mean:", round(sum(values)/len(values), 2),
          "median:", median(values),
          "max:", max(values))

print("\nCONFIDENCE DISTRIBUTION")
for sensor, counts in confidence.items():
    print(sensor, dict(counts))
