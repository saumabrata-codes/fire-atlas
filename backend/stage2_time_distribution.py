import csv
from collections import Counter, defaultdict

INPUT_FILE = r"..\india_firms_january_2025.csv"

hourly = defaultdict(Counter)
daily_hourly = defaultdict(lambda: defaultdict(Counter))
time_formats = Counter()

with open(INPUT_FILE, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        sensor = row["instrument"]
        raw_time = row["acquisition_time"].strip()

        time_formats[len(raw_time)] += 1

        hhmm = raw_time.zfill(4)
        hour = int(hhmm[:2])

        if not 0 <= hour <= 23:
            continue

        hourly[sensor][hour] += 1
        daily_hourly[row["acquisition_date"]][sensor][hour] += 1

print("ACQUISITION TIME FORMAT COUNTS")
print(dict(time_formats))

print("\nHOURLY DETECTION DISTRIBUTION")
print(f"{'HOUR':<8}{'MODIS':>12}{'VIIRS':>12}")

for hour in range(24):
    print(
        f"{hour:02d}:00"
        f"{hourly['MODIS'][hour]:>12}"
        f"{hourly['VIIRS'][hour]:>12}"
    )

print("\nTOTALS")
for sensor in ["MODIS", "VIIRS"]:
    print(sensor, "records:", sum(hourly[sensor].values()),
          "hours represented:", len(hourly[sensor]))

print("\nDAYS WITH BOTH SENSORS IN THE SAME UTC HOUR")
same_hour_days = 0

for date, sensors in sorted(daily_hourly.items()):
    common = set(sensors["MODIS"]) & set(sensors["VIIRS"])
    if common:
        same_hour_days += 1

print(same_hour_days, "out of", len(daily_hourly))
