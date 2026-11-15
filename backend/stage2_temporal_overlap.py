import csv
from collections import defaultdict, Counter

INPUT_FILE = r"..\india_firms_january_2025.csv"

daily_bins = defaultdict(lambda: defaultdict(Counter))
invalid_times = []

with open(INPUT_FILE, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        raw = row["acquisition_time"].strip().zfill(4)

        try:
            hour = int(raw[:2])
            minute = int(raw[2:])

            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid HHMM")

            total_minutes = hour * 60 + minute
            bin_start = (total_minutes // 30) * 30
            bin_label = f"{bin_start // 60:02d}:{bin_start % 60:02d}"

            daily_bins[row["acquisition_date"]][row["instrument"]][bin_label] += 1

        except ValueError:
            invalid_times.append(row["acquisition_time"])

shared_bins = 0
modis_only_bins = 0
viirs_only_bins = 0
shared_days = 0

for date, sensors in sorted(daily_bins.items()):
    modis = set(sensors["MODIS"])
    viirs = set(sensors["VIIRS"])

    common = modis & viirs
    shared_bins += len(common)
    modis_only_bins += len(modis - viirs)
    viirs_only_bins += len(viirs - modis)

    if common:
        shared_days += 1

print("30-MINUTE TEMPORAL OVERLAP")
print("Dates analysed:", len(daily_bins))
print("Dates with common 30-minute bins:", shared_days)
print("Shared date-bin combinations:", shared_bins)
print("MODIS-only date-bin combinations:", modis_only_bins)
print("VIIRS-only date-bin combinations:", viirs_only_bins)
print("Invalid acquisition times:", len(invalid_times))

print("\nSHARED BINS BY DATE")
for date, sensors in sorted(daily_bins.items()):
    common = sorted(
        set(sensors["MODIS"]) & set(sensors["VIIRS"])
    )
    if common:
        print(date, ", ".join(common))
