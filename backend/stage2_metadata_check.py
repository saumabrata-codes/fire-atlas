import csv
from collections import Counter, defaultdict

path = r"..\india_firms_january_2025.csv"

versions = defaultdict(Counter)
satellites = defaultdict(Counter)
datasets = Counter()
rows = 0
exact_rows = Counter()
invalid_coordinates = 0
invalid_frp = 0

with open(path, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        rows += 1

        sensor = row["instrument"]
        versions[sensor][row["version"]] += 1
        satellites[sensor][row["satellite"]] += 1
        datasets[row["source_dataset"]] += 1

        exact_key = (
            row["instrument"],
            row["satellite"],
            row["acquisition_date"],
            row["acquisition_time"],
            row["latitude"],
            row["longitude"],
            row["frp"]
        )
        exact_rows[exact_key] += 1

        lat = float(row["latitude"])
        lon = float(row["longitude"])
        frp = float(row["frp"])

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            invalid_coordinates += 1

        if frp < 0:
            invalid_frp += 1

print("TOTAL ROWS:", rows)

print("\nPRODUCT VERSIONS")
for sensor, counts in versions.items():
    print(sensor, dict(counts))

print("\nSATELLITES")
for sensor, counts in satellites.items():
    print(sensor, dict(counts))

print("\nSOURCE DATASETS")
print(dict(datasets))

print("\nDUPLICATE CHECK")
print("Exact duplicate groups:", sum(v > 1 for v in exact_rows.values()))
print("Rows involved in duplicates:", sum(v for v in exact_rows.values() if v > 1))

print("\nVALIDATION")
print("Invalid coordinates:", invalid_coordinates)
print("Negative FRP:", invalid_frp)
