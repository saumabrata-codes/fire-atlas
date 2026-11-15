import csv
from pathlib import Path

from app.analytics.harmonization.grid_overlap import (
    analyze_grid_sensitivity,
)

INPUT_FILE = Path(__file__).resolve().parents[1] / "india_firms_january_2025.csv"

if not INPUT_FILE.exists():
    raise FileNotFoundError(f"Dataset not found: {INPUT_FILE}")

with INPUT_FILE.open(newline="", encoding="utf-8-sig") as file:
    observations = list(csv.DictReader(file))

results = analyze_grid_sensitivity(
    observations,
    (1000, 5000, 10000),
)

print("GRID RESOLUTION SENSITIVITY — TESTED MODULE")
print("-" * 76)
print(f"{'GRID':<12}{'TOTAL':>10}{'SHARED':>10}{'MODIS ONLY':>14}{'VIIRS ONLY':>14}{'OVERLAP %':>14}")

for result in results:
    print(
        f"{result['grid_size_m'] // 1000} km"
        f"{result['total_grid_days']:>10}"
        f"{result['shared']:>10}"
        f"{result['modis_only']:>14}"
        f"{result['viirs_only']:>14}"
        f"{result['overlap_percent']:>13.2f}%"
    )

expected = {
    1000: (35548, 1131, 4986, 29431, 3.18),
    5000: (27331, 1625, 3475, 22231, 5.95),
    10000: (24095, 1840, 2923, 19332, 7.64),
}

print("\nBASELINE COMPARISON")
for result in results:
    size = result["grid_size_m"]
    actual = (
        result["total_grid_days"],
        result["shared"],
        result["modis_only"],
        result["viirs_only"],
        result["overlap_percent"],
    )
    status = "PASS" if actual == expected[size] else "MISMATCH"
    print(f"{size // 1000} km: {status}")

if any(
    (
        r["total_grid_days"],
        r["shared"],
        r["modis_only"],
        r["viirs_only"],
        r["overlap_percent"],
    ) != expected[r["grid_size_m"]]
    for r in results
):
    raise SystemExit("Baseline comparison failed.")

