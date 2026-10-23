# Verification record

Verified locally on 22 October 2026 (America/Toronto).

- `pytest -q -p no:cacheprovider`: 96 passing tests, including every selectable Ontario location's saved-data model, exact local AQHI area filtering, missing-AQHI behaviour, latest forecast publication, Western Ontario time zones, region selection, all seven offline pages, native Power BI project integrity and scenario-interval parity with Python OLS. The optional pytest cache is disabled to avoid a local Windows cache-directory ownership warning.
- `ruff check .`: passed, including the executed notebook. Notebook import placement permits root-path setup before local imports.
- `python scripts/verify_live.py`: all 47 Ontario locations retrieved live weather and ozone, with live AQHI for all 41 configured official areas; six additional northern communities correctly return unavailable AQHI without proxy substitution. All seven pages and the entry point executed without exceptions. Detailed source timestamps and results are in `live_verification.json`.
- Streamlit server started locally on port 8501. Browser review covered region switching to Eastern Ontario, loading Belleville and then Ottawa with each location's own AQHI, and the existing responsive layout. The current screenshot shows Ottawa: `screenshot.png`.
- Canonical R dataset downloaded using statsmodels and preserved with provenance. Notebook cells were executed against the saved canonical data.

## Findings requiring attention

The supplied historical reference was independently reproduced from canonical R data: mean-imputed OLS uses 153 rows and has R² 0.480025, matching its rounded coefficients. The primary complete-case model uses 111 rows and has R² 0.605895. The Method page, notebook and `baseline_sensitivity.csv` expose the difference without treating filled responses as observed validation targets. Comparisons across changed samples are descriptive, not evidence of comparative predictive skill. No original reference file was modified or included in the portfolio bundle.

All 47 saved models use 90 complete days. Training R² ranges from 0.093 to 0.718, with no fit below 0.05 or above 0.95. The saved Toronto model remains R² 0.461, adjusted R² 0.442, chronological holdout RMSE 7.51 ppb. Of the 47 saved holdouts, 46 contain zero event days at 60 ppb, so recall at that cutoff cannot be estimated for those locations. Good average prediction error does not establish alert performance.

Toronto residual Shapiro–Wilk p is approximately 0.000194. Normal residual assumptions are questionable; serial dependence and forecast error also limit nominal OLS intervals. Reference ozone comes from CAMS, not station monitors. These limitations are visible in the app and README.

## Endpoints and adaptations

Weather forecast: `https://api.open-meteo.com/v1/forecast`.
Weather history: `https://archive-api.open-meteo.com/v1/archive`.
Ozone: `https://air-quality-api.open-meteo.com/v1/air-quality`.
AQHI: `https://api.weather.gc.ca/collections/aqhi-observations-realtime/items` and `https://api.weather.gc.ca/collections/aqhi-forecasts-realtime/items`.
Baseline: statsmodels `get_rdataset('airquality', 'datasets')`.
Ontario area metadata: `https://api.weather.gc.ca/collections/aqhi-stations/items`.
Additional community coordinates and time zones: `https://geocoding-api.open-meteo.com/v1/search` (GeoNames via Open-Meteo).

Core data endpoints are unchanged. The expansion adds station and geocoding metadata endpoints and replaces the Toronto bounding-box AQHI parameters with exact `location_id` filters and `latest=true` observations. Forecast displays retain only the newest publication. Location-specific IANA time zones include America/Winnipeg for Western Ontario points. UTC epochs avoid DST ambiguity; recent forecasts fill archive publication gaps. An eight-day UTC weather request supplies seven complete local forecast days. Stale snapshots retain their dates and do not become today's predictions.

## Remaining external steps / verification limits

No GitHub remote was selected or created, no hosted CI run was executed, and no Streamlit Community Cloud app was deployed. The README includes deployment instructions and placeholders for the live URL and author's exact LinkedIn profile. Local testing used the available Python 3.12 runtime; Python 3.11 is configured as the CI/deployment target and was not executed locally. Local Windows application control blocked newer PyArrow and unused statsmodels state-space DLLs; compatible PyArrow 19 and targeted imports resolved execution without changing security settings.
