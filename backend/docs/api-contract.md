

\# FIRE ATLAS — Backend API Contract



Version: 1.0

Status: Development / Mock Data



\## 1. Overview



This document defines the communication contract between the FIRE ATLAS

frontend and backend.



The backend provides four dashboard APIs:



| API | Method | Endpoint | Purpose |

|---|---|---|---|

| Overview | POST | /api/v1/overview | Dashboard statistics |

| Map | POST | /api/v1/map | Geographic hotspot records |

| Sensor Comparison | POST | /api/v1/sensors | MODIS vs VIIRS comparison |

| Calendar | POST | /api/v1/calendar | Fire activity calendar |



Base URL (local development):



http://127.0.0.1:8000



All request bodies use JSON.



\## 2. Common Request Contract



All four endpoints use the same DataFilter request structure.



Example — Global selection:



{

&#x20; "start\_date": "2026-11-10",

&#x20; "end\_date": "2026-11-12",

&#x20; "geography": {

&#x20;   "selection\_type": "global"

&#x20; },

&#x20; "sensors": \["MODIS", "VIIRS"],

&#x20; "aggregation": "daily"

}



Example — Bounding box selection:



{

&#x20; "start\_date": "2026-11-10",

&#x20; "end\_date": "2026-11-12",

&#x20; "geography": {

&#x20;   "selection\_type": "bounding\_box",

&#x20;   "bbox": {

&#x20;     "west": 68,

&#x20;     "south": 6,

&#x20;     "east": 98,

&#x20;     "north": 37

&#x20;   }

&#x20; },

&#x20; "sensors": \["MODIS", "VIIRS"],

&#x20; "aggregation": "monthly"

}



\### Request fields



| Field | Description |

|---|---|

| start\_date | Start date of requested data |

| end\_date | End date of requested data |

| geography.selection\_type | global or bounding\_box |

| geography.bbox | Geographic coordinates when bounding\_box is selected |

| sensors | MODIS, VIIRS or both |

| aggregation | daily, monthly or yearly |



Date format: YYYY-MM-DD



Period formats:

\- Daily: YYYY-MM-DD

\- Monthly: YYYY-MM

\- Yearly: YYYY



\## 3. Overview API



Endpoint: POST /api/v1/overview



Purpose:

Returns the overall hotspot detection statistics for the selected

geographic region and date range.



Example response:



{

&#x20; "requested\_start\_date": "2026-11-10",

&#x20; "requested\_end\_date": "2026-11-12",

&#x20; "summary": {

&#x20;   "total\_hotspot\_detections": 6,

&#x20;   "sensor\_counts": {

&#x20;     "MODIS": 3,

&#x20;     "VIIRS": 3

&#x20;   },

&#x20;   "activity\_summary": \[

&#x20;     {

&#x20;       "period": "2026-11-10",

&#x20;       "detection\_count": 2

&#x20;     },

&#x20;     {

&#x20;       "period": "2026-11-11",

&#x20;       "detection\_count": 2

&#x20;     },

&#x20;     {

&#x20;       "period": "2026-11-12",

&#x20;       "detection\_count": 2

&#x20;     }

&#x20;   ],

&#x20;   "frp\_summary": {

&#x20;     "mean\_frp\_mw": 11.33,

&#x20;     "max\_frp\_mw": 18.7,

&#x20;     "observations\_with\_frp": 6

&#x20;   }

&#x20; },

&#x20; "metadata": {}

}



Frontend usage:

\- Total hotspot detection cards.

\- MODIS and VIIRS count cards.

\- Activity trend chart.

\- FRP statistics.



\## 4. Map API



Endpoint: POST /api/v1/map



Purpose:

Returns individual hotspot records for plotting on the geographic map.



Example response:



{

&#x20; "records": \[

&#x20;   {

&#x20;     "source\_record\_id": "example-001",

&#x20;     "sensor": "MODIS",

&#x20;     "observed\_date": "2026-11-10",

&#x20;     "latitude": 22.5726,

&#x20;     "longitude": 88.3639,

&#x20;     "frp\_mw": 12.4,

&#x20;     "source\_product": "SYNTHETIC\_MODIS",

&#x20;     "confidence": null,

&#x20;     "is\_synthetic": true,

&#x20;     "source\_attributes": {}

&#x20;   }

&#x20; ],

&#x20; "metadata": {}

}



Frontend usage:

\- Plot latitude and longitude on the map.

\- Display sensor-specific markers.

\- Show FRP and source details when a marker is selected.

\- Filter map records by selected region and dates.



\## 5. Sensor Comparison API



Endpoint: POST /api/v1/sensors



Purpose:

Compares MODIS and VIIRS hotspot detections and returns

sensor-wise statistics and time-series data.



Example response:



{

&#x20; "requested\_start\_date": "2026-11-10",

&#x20; "requested\_end\_date": "2026-11-12",

&#x20; "comparison": {

&#x20;   "total\_hotspot\_detections": 6,

&#x20;   "sensor\_counts": {

&#x20;     "MODIS": 3,

&#x20;     "VIIRS": 3

&#x20;   },

&#x20;   "sensor\_summaries": {

&#x20;     "MODIS": {

&#x20;       "detection\_share\_percent": 50.0,

&#x20;       "mean\_frp\_mw": 13.57,

&#x20;       "max\_frp\_mw": 18.7,

&#x20;       "observations\_with\_frp": 3

&#x20;     },

&#x20;     "VIIRS": {

&#x20;       "detection\_share\_percent": 50.0,

&#x20;       "mean\_frp\_mw": 9.1,

&#x20;       "max\_frp\_mw": 14.2,

&#x20;       "observations\_with\_frp": 3

&#x20;     }

&#x20;   }

&#x20; },

&#x20; "time\_series": \[

&#x20;   {

&#x20;     "period": "2026-11-10",

&#x20;     "MODIS": 1,

&#x20;     "VIIRS": 1,

&#x20;     "total\_detections": 2

&#x20;   }

&#x20; ],

&#x20; "product\_summaries": \[

&#x20;   {

&#x20;     "source\_product": "SYNTHETIC\_MODIS",

&#x20;     "sensor": "MODIS",

&#x20;     "detection\_count": 3

&#x20;   }

&#x20; ],

&#x20; "metadata": {}

}



Frontend usage:

\- MODIS vs VIIRS comparison chart.

\- Sensor detection share chart.

\- Mean and maximum FRP comparison.

\- Daily, monthly and yearly sensor trend charts.

\- Product-wise comparison.



\## 6. Calendar API



Endpoint: POST /api/v1/calendar



Purpose:

Returns fire activity grouped by the aggregation selected in the request.



Example response:



{

&#x20; "requested\_start\_date": "2026-11-10",

&#x20; "requested\_end\_date": "2026-11-12",

&#x20; "aggregation": "daily",

&#x20; "calendar\_periods": \[

&#x20;   {

&#x20;     "period": "2026-11-10",

&#x20;     "MODIS": 1,

&#x20;     "VIIRS": 1,

&#x20;     "total\_detections": 2,

&#x20;     "status": "observed\_with\_detections"

&#x20;   },

&#x20;   {

&#x20;     "period": "2026-11-11",

&#x20;     "MODIS": 1,

&#x20;     "VIIRS": 1,

&#x20;     "total\_detections": 2,

&#x20;     "status": "observed\_with\_detections"

&#x20;   }

&#x20; ],

&#x20; "activity\_summary": {

&#x20;   "total\_detections": 6,

&#x20;   "periods\_with\_detections": 3,

&#x20;   "highest\_activity\_period": "2026-11-10",

&#x20;   "highest\_activity\_detections": 2

&#x20; },

&#x20; "sensor\_summary": {

&#x20;   "MODIS": 3,

&#x20;   "VIIRS": 3

&#x20; },

&#x20; "metadata": {}

}



Frontend usage:

\- Daily/monthly/yearly activity calendar.

\- Highlight high-activity periods.

\- Show sensor-wise detections.

\- Display period status.



Supported calendar statuses:



\- observed\_with\_detections

\- observed\_zero\_detections

\- missing

\- incomplete



Important:

Missing observations must not be interpreted as zero detections.

Coverage-based statuses require verified provider availability data.



\## 7. Common Metadata Contract



The APIs reuse DataMetadata.



Expected fields:



{

&#x20; "provider": "mock",

&#x20; "is\_synthetic": true,

&#x20; "requested\_start\_date": "2026-11-10",

&#x20; "requested\_end\_date": "2026-11-12",

&#x20; "sensors\_requested": \["MODIS", "VIIRS"],

&#x20; "records\_returned": 6,

&#x20; "sensor\_record\_counts": {

&#x20;   "MODIS": 3,

&#x20;   "VIIRS": 3

&#x20; },

&#x20; "data\_status": "available",

&#x20; "note": "Synthetic development data"

}



Data status values:



\- available

\- no\_data

\- partial

\- unavailable

\- no\_matching\_records



\## 8. Error Handling



The backend uses a standardized error response.



Illustrative example:



{

&#x20; "error": {

&#x20;   "code": "VALIDATION\_ERROR",

&#x20;   "message": "Request validation failed"

&#x20; }

}



The frontend should handle HTTP errors:



| HTTP status | Meaning |

|---|---|

| 400 | Bad request |

| 422 | Request validation error |

| 503 | Data unavailable |

| 500 | Unexpected server error |



Use the actual error response structure returned by the backend.



\## 9. Scientific and Data Interpretation Rules



1\. A hotspot detection is not necessarily a unique fire.

2\. Do not label detection counts as unique fire counts.

3\. FRP represents fire radiative power in MW.

4\. Keep MODIS and VIIRS detection counts separate.

5\. Do not treat missing data as zero detections.

6\. Preserve source product information.

7\. Clearly identify synthetic data during development.

8\. Do not infer sensor availability from detection counts.



\## 10. Current Integration Status



The four APIs currently use the mock data provider.



Real NASA FIRMS provider integration, verified

sensor availability and harmonization are pending.



Response examples in this document are illustrative.

The actual Pydantic schemas and running Swagger responses

are the authoritative implementation contract.



