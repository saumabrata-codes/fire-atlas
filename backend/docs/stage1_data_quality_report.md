# FIRE ATLAS — Stage 1 Data Quality Report

## 1. Dataset inventory

- Region: Asia
- Period: January 2021 – August 2026
- Monthly CSV files: 68
- Total observations: 25,239,782
- Total dataset size: approximately 9.2 GB
- All 68 files were read successfully.
- All 68 files have the same 18-column schema.

## 2. Temporal coverage

- 2021–2025: 12 monthly files per year.
- 2026: January–August files available.
- September–December 2026 files are absent from the archive.
- Acquisition dates were observed across the expected months in the monthly coverage audit.

## 3. Sensor coverage

- MODIS: 4,288,301 observations.
- VIIRS SNPP: 20,951,481 observations.
- Both sensors are represented in every month from January 2021 through July 2026.
- August 2026 contains 154,823 MODIS observations and no VIIRS observations.
- August VIIRS absence is confirmed in the stored archive; its collection cause remains unverified.

## 4. Product and version distribution

| Product | Version | Rows |
|---|---|---:|
| MODIS_SP | 6.03 | 1,492,430 |
| MODIS_SP | 61.03 | 2,795,871 |
| VIIRS_SNPP_SP | 2 | 20,951,481 |

Version identifiers were observed and counted. Their scientific meaning and compatibility require confirmation against authoritative product metadata.

## 5. Schema

The common CSV schema contains:

latitude, longitude, acquisition_date, acquisition_time, satellite, instrument, source_dataset, brightness, bright_t31, bright_ti4, bright_ti5, scan, track, confidence, frp, daynight, version, raw_properties.

All 68 files have identical column names and ordering.

## 6. Data validation

The streaming audit reported:

- Missing latitude, longitude, acquisition date, acquisition time, satellite, instrument, source dataset, scan, track, confidence, FRP, day/night, version and raw properties: zero.
- MODIS-specific brightness fields are absent on VIIRS rows.
- VIIRS-specific brightness fields are absent on MODIS rows.
- Invalid numeric values: zero.
- Invalid acquisition dates: zero.
- Invalid acquisition times: zero.
- Out-of-range coordinates: zero.
- Negative FRP values: zero.

The sensor-specific missing brightness fields are expected from the observed sensor-specific schema and must remain nullable.

Confidence representations differ between sensors and must not be treated as a shared numeric scale without justification.

## 7. Backend model compatibility

The existing FireObservation model was tested against one actual MODIS row and one actual VIIRS row using from_processed_row.

Both conversions passed. The test confirmed date parsing, product/version retention, FRP parsing and raw_properties preservation.

The model has coordinate and FRP validation.

Acquisition time is currently preserved as a string; UTC normalization remains a later task.

## 8. Test suite

Backend tests: 59 passed.

One Starlette/httpx deprecation warning was reported. It did not cause test failures.

## 9. Limitations and unresolved items

1. August 2026 VIIRS observations are absent. Collection logs are required to determine why.
2. MODIS version identifiers 6.03 and 61.03 require authoritative metadata confirmation.
3. The metadata script's duplicate check covered a 45,403-row January 2025 sample, not all 25.24 million rows.
4. The initial filename/date mismatch count was produced by an incorrect filename comparison and must not be interpreted as a data-quality failure.
5. Abhirup's collection repository and logs have not yet been reviewed.
6. Full historical integration and end-to-end validation remain pending.

## 10. Stage 1 status

The inventory, filename coverage, sensor coverage, version distribution, schema consistency and sample model conversion checks have been performed.

Final sign-off remains conditional on:
- authoritative product metadata confirmation;
- review of Abhirup's collection pipeline and August VIIRS logs;
- agreement on the common observation contract.
