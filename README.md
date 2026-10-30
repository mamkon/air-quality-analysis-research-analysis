# Ontario Air Quality Predictive Analytics & Decision-Support Framework

**Predictive Analytics | Public Health Analytics | Decision Support | Risk Modelling**

## Overview

This research explores how predictive analytics can support environmental and public-health planning.

Using data for **47 selected Ontario locations**, I developed a research solution that combines Python statistical analysis with an interactive Power BI dashboard. The work brings together geospatial comparison, weather-based ozone prediction, chronological model validation, uncertainty assessment, decision analysis and scenario modelling.

The purpose is to move from describing conditions to asking what might happen next, how much confidence to place in a prediction, and what further evidence is needed before acting. The dashboard is a dated research snapshot, not an operational early-warning system or an official health advisory.

## Business Problem

Air-quality events raise planning questions for public-health teams, municipalities, schools, outdoor employers and healthcare organisations. A historical chart can show what happened, but planning also requires questions such as:

- **What might happen next?** Estimate afternoon ozone using weather conditions.
- **How reliable is the estimate?** Examine later-day validation, errors and prediction bounds.
- **What responses should be considered?** Explore the trade-off between missed events and false alarms.
- **What changes under another scenario?** Compare illustrative temperature, wind and solar-radiation inputs.

This research explores those analytical questions. It does not establish the clinical effectiveness of a response or replace official AQHI guidance.

## Explore the Research

- [Project Website](https://mamkon.github.io/air-quality-analysis-research-analysis/)
- [Download the Power BI Dashboard](powerbi/AIR%20QUALITY%20ANALYSIS%20RESEARCH%20ANALYSIS.pbix) — open in Power BI Desktop and select one location on Overview.
- [Power BI Opening and Refresh Guide](powerbi/README.md)
- [Research Notebook](notebooks/research_reviewed.ipynb)
- [Plain Language Guide](docs/plain_language_guide.md)
- [Full Research Outline](docs/research_outline.md)

Power BI presents the imported snapshot from sources retrieved on **23 October 2026**. The Python/Streamlit application contains the API integration; it requires separate deployment to provide a hosted live app. GitHub Pages presents the research and downloads, rather than running Power BI.

## Skills Demonstrated

| Area | Evidence in This Research |
|---|---|
| Predictive Analytics and Forecasting | Weather-based multiple linear regression for afternoon ozone |
| Time-Series Data Preparation | Time-zone-aware hourly-to-daily alignment, chronological splitting and rolling error assessment; the fitted model is OLS, not a dedicated time-series forecasting model |
| Statistical Validation and Uncertainty | Later-day holdout evaluation, residual diagnostics and conditional 95% OLS prediction intervals |
| Risk Assessment and Decision Support | Threshold-based event evaluation, precision/recall and missed-event versus false-alarm trade-offs |
| Scenario Modelling | What-if weather inputs, prediction bounds and training-range checks |
| Power BI, DAX and Power Query | Native visuals, measures, import transformations, relationships and scenario calculations |
| ETL and Data Modelling | API integration, unit conversion, missing-data handling, source timestamps and reproducible exports |
| Geospatial Analysis and Azure Maps | Reviewed location coordinates, regional filtering and comparison across selected Ontario points |
| Performance Measurement and Data Storytelling | Model and decision metrics, plain-language explanations, dashboard formatting and source transparency |
| Public Health and Healthcare Analytics | Framing environmental planning questions and explaining potential healthcare adaptations, without claiming patient-outcome validation |

## Dashboard Capabilities

### Ontario-Wide Air Quality Monitoring

The map and location selectors support comparison across selected points in Ontario and show geographic variation in modelled ozone reference conditions. The 47 locations do not represent complete monitoring coverage of every community.

### Forecasting and Risk Outlook

Weather-based models estimate afternoon ozone, with upper and lower prediction bounds shown alongside the estimates. These bounds are conditional on OLS assumptions and do not include all weather, emissions or CAMS uncertainty. Official AQHI and illustrative ozone thresholds remain separate measures.

### Model Validation and Performance Assessment

Chronological validation separates training days from later testing days to reduce optimistic evaluation. The validation target is modelled CAMS reference ozone. Retrospective archive weather is not equivalent to testing archived forecast vintages, and short seasonal windows do not establish year-round forecast performance.

### Decision-Support Framework

The research examines event thresholds, missed events and false alarms to show how model evaluation connects to planning choices. Unsupported precision or recall remains undefined when the data contain no relevant events. The framework illustrates trade-offs; it does not prescribe or validate operational health actions.

### Scenario Planning and What-If Analysis

The simulator explores how different temperature, wind and sunlight inputs change estimated ozone. It includes prediction bounds and flags inputs outside the training range. These are conditional model scenarios, not causal estimates of the effect of changing the environment.

## Healthcare and Public Health Relevance

Although this research uses environmental data, its analytical workflow offers a starting point for exploring other public-health and healthcare questions:

- Disease surveillance and population-health monitoring.
- Emergency department demand forecasting.
- Healthcare resource planning.
- Early-warning and risk-prediction research.

Each adaptation would require suitable domain data, governance, outcome definitions and independent validation. **This research contains no patient data and does not demonstrate predictions of illness, hospital demand or individual health risk.**

My interest is in using predictive analytics to help healthcare organisations identify emerging risks, understand patterns in complex data and support evidence-based planning.

## Target Audience and Stakeholders

The primary audience includes public-health analysts, environmental researchers, municipal analytics teams, healthcare planning professionals and hiring managers assessing analytical and decision-support skills.

Wider stakeholders include Ontario residents, people more vulnerable to poor air quality, schools and outdoor employers. Their needs motivate clear communication; real health and activity decisions should follow official AQHI and public-health advice.

## Key Lessons Learned

- Prediction accuracy alone does not establish readiness for action.
- Validation must be transparent about dates, targets and data limitations.
- Decision-makers need uncertainty information alongside a forecast.
- Analytics becomes more useful when model performance is connected to planning trade-offs.
- Clear explanations, accessible visuals and thoughtful formatting are part of communicating the research.

## About the Author

I am **Mercy Mamkon Oyeleke**, a Data Analytics and Business Intelligence Consultant with more than 15 years of experience across banking, finance, analytics and business intelligence. Through analytics consulting and graduate studies in Big Data and Predictive Analytics, I focus on transforming complex data into useful insights, with an emerging interest in healthcare and public health.

## Research Evidence and Reproducibility

### Research Aim and Objectives

This research examines how temperature, wind speed and sunlight relate to ground-level ozone, and whether these relationships can help estimate afternoon ozone in selected Ontario locations.

The objectives are to understand the data, explain missing-data choices, explore weather and ozone relationships, compare regression methods, check predictions on later days, and explain practical uses and limitations.

See the [full research outline](docs/research_outline.md) for the reasons, research questions and section plan.

### Why This Subject, and Who Could Use It?

This research focuses on **air quality and public-health planning** to turn environmental data into information that can support practical planning. Ontario was selected to make the work relevant to communities across the province. Comparing 47 locations shows local differences instead of treating the whole province as one place. Ground-level ozone was selected because weather helps explain how it forms and moves. Sunlight helps gases in the air react to form ozone; temperature and wind also matter. See [ECCC's explanation](https://www.canada.ca/en/environment-climate-change/services/air-quality-health-index/weather.html).

| Industry or team | Example use of air-quality data |
|---|---|
| Public health | Prepare messages using official air-quality advice |
| Hospitals | Explore links with breathing-related visits using separate patient data |
| Schools and childcare | Check official AQHI when planning outdoor activities |
| Construction and outdoor employers | Review outdoor work timing and breaks alongside official guidance |
| Government and environmental consulting | Compare locations and identify monitoring needs |
| Transport and city planning | Study outdoor exposure using additional local data |
| Pharmacies and suppliers | Compare air-quality patterns with actual sales before changing stock |
| Insurance and risk teams | Add environmental context to wider risk studies |

These are possible uses of this type of data. They are not claims that organisations use this dashboard or that the project has proved these benefits.

### How The Weather Helps Prediction

This research demonstrates my skills in preparing data, finding patterns, checking predictions and explaining results. Multiple linear regression was selected as a clear starting method because its results can be explained and reviewed. It does not prove cause and effect or guarantee the best possible forecast.

The model learns a pattern from past **temperature, wind speed, sunlight energy and ozone** for the same location and day. It uses the three weather inputs together to estimate afternoon ozone. The model then uses forecast weather to make an estimate for a future day.

For example, it checks the pattern learned from previous warm, sunny days, together with wind. Sunshine alone does not guarantee high ozone. Emissions and pollution arriving from elsewhere also matter. This research checks predictions against a later part of the past data that was kept out of training.

Ontario training ozone comes from CAMS through Open-Meteo: these are model estimates, not direct station readings. The project predicts ozone, not hospital visits or individual illness. The 1973 New York data explain the method only; recent Ontario data train the modern models. Use official AQHI and local advice for health decisions.

Read the [plain-English guide](docs/plain_language_guide.md) for examples and simple definitions. Technical details follow below. The [reviewed research notebook](notebooks/research_reviewed.ipynb) contains the cleaned outline and executed historical analysis.

### Research Workflow Pipeline

![Process flow showing separate historical analysis and Ontario data collection, preparation, prediction checks, forecasting and dashboard steps](docs/workflow_pipeline.png)

The image shows how this research moves from source data to estimates and planning information. The historical method is separate from the Ontario prediction model.

### Key Findings — Generated From Saved Real-source Data

- Historical baseline: **111 complete cases**, adjusted R² **0.595**.
- Modern Toronto model: **90 complete days**, adjusted R² **0.437**.
- Chronological holdout RMSE: **7.39 ppb**. At the illustrative 60 ppb cutoff, the holdout contains **0 event days**; unsupported recall is undefined.

These are dated snapshot findings, not promised live performance. Regenerate them with `python scripts/build_docs.py`; inspect [computed evidence](docs/results.json) and [live verification](docs/live_verification.json).

![Executive overview](docs/screenshot.png)

### Sources and Attribution

| Source | Endpoint / provenance | Use |
|---|---|---|
| R airquality | `statsmodels.datasets.get_rdataset('airquality', 'datasets')`; [R documentation](https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/airquality.html) | NYC May–September 1973 method demonstration |
| Open-Meteo weather forecast | `https://api.open-meteo.com/v1/forecast` | hourly `temperature_2m,wind_speed_10m,shortwave_radiation`, `past_days=7`, `forecast_days=8`, `wind_speed_unit=kmh` |
| Open-Meteo weather archive | `https://archive-api.open-meteo.com/v1/archive` | explicit start/end dates, same variables; ends five days before request date to accommodate reanalysis lag |
| Open-Meteo / CAMS air quality | `https://air-quality-api.open-meteo.com/v1/air-quality` | hourly `ozone`, `past_days=92`, `forecast_days=5`; modelled concentrations, not station measurements |
| ECCC MSC GeoMet | `https://api.weather.gc.ca/collections/aqhi-observations-realtime/items` and `aqhi-forecasts-realtime/items` | Exact selected `location_id`, `f=json`, `limit=1000`; `latest=true` for observations; latest forecast publication retained separately |

The selector covers **47 Ontario locations across 6 regions**, including all 41 Ontario areas listed by ECCC AQHI plus Kenora, Dryden, Sioux Lookout, Timmins, Moosonee and Fort Severn. These are representative point estimates, not continuous station coverage of every address. Official AQHI is shown only for the matching configured ECCC area; the six additional communities explicitly show AQHI as unavailable. No Toronto value is substituted.

All Open-Meteo requests use `timezone=UTC,timeformat=unixtime` then convert epochs to the selected location's IANA time zone. Western locations such as Kenora use America/Winnipeg. `data/ontario_locations.json` stores coordinates, region, time zone, AQHI area ID and retrieval time, loaded through `src/config.py`. Original city-centre weather points are retained for the first five locations; other official areas use ECCC point coordinates. Weather grid cells and AQHI monitoring areas are distinct spatial supports.

Metadata sources: [ECCC AQHI stations](https://api.weather.gc.ca/collections/aqhi-stations?f=json) and [Open-Meteo geocoding / GeoNames](https://open-meteo.com/en/docs/geocoding-api). Refresh and review with `python scripts/build_locations.py`. Station filters replace the previous Toronto bounding-box query, avoiding mixed stations and truncated province-wide result sets. The core forecast, archive, ozone and AQHI endpoints remain the same; the expansion adds station-catalogue and geocoding metadata endpoints.

Official documentation checked: [forecast](https://open-meteo.com/en/docs), [historical weather](https://open-meteo.com/en/docs/historical-weather-api), [air quality](https://open-meteo.com/en/docs/air-quality-api), [ECCC observations](https://api.weather.gc.ca/collections/aqhi-observations-realtime?f=json), [ECCC forecasts](https://api.weather.gc.ca/collections/aqhi-forecasts-realtime?f=json).

No endpoint replacement was necessary. Implementation adaptations: UTC epoch conversion for DST, archive-to-forecast gap filling, and explicit recognition that CAMS is modelled data. Open-Meteo's keyless free API is for non-commercial use and has usage limits; assess provider terms before commercial deployment. Attribution: Open-Meteo and CAMS / Copernicus, CC BY 4.0; ECCC Open Government Licence – Canada. The project code is MIT; source data retain their original terms.

### Methodology

1. Demonstrate missing-data sensitivity, Pearson/Spearman correlation, Shapiro–Wilk, simple/multiple OLS, VIF, residual and Q–Q diagnostics on historical data. Complete cases are the primary baseline; imputation is descriptive sensitivity analysis.
2. Aggregate modern weather into local daily maximum temperature (°C), mean wind (km/h), total shortwave radiation (MJ/m²/day). Each hourly radiation mean is multiplied by 0.0036. Require complete local days, including 23/25-hour DST days.
3. Define daily ozone as the mean of local hourly samples at 13:00, 14:00 and 15:00, requiring all samples. Convert µg/m³ to ppb by dividing by 1.96, assuming 25°C and 1 atm. The API's hourly sampling is an approximation to the historical afternoon measurement window.
4. Join on local day; use only dates before today, at most the latest 90 complete cases. Never score modern SI inputs with the historical °F/mph/Langleys model. Narrow-band historical Langleys are not treated as equivalent to modern broadband radiation.
5. Hold out the latest quarter chronologically. Refit the deployment OLS on all past days. Held-out residuals drive confusion matrices and rolling seven-day RMSE. Archive weather validation is retrospective, not a test against archived forecast vintages.
6. Show raw 95% individual prediction intervals. Negative values expose OLS limitations rather than being silently clipped. Log-response AIC/BIC, R² and RMSE are explicitly on a different scale and not ranked against raw-response statistics.

**Missing-data reconciliation:** mean-imputed historical OLS uses 153 rows with R² 0.480; the requested primary analysis uses 111 complete cases. The [computed comparison](docs/baseline_sensitivity.csv) includes mean/median alternatives, coefficients and the number of filled ozone responses. These approaches change sample composition and variability, so their training R² values do not establish comparative predictive skill. Filled responses are never used as live validation targets. The **Background & Method** page and reproducible notebook expose this distinction.

API calls are cached one hour for live data and one day for archive/baseline data. Requests have bounded timeouts and retries. Every city has genuine timestamped JSON snapshots, plus derived daily CSVs; API errors display a fallback banner. Snapshot dates are never shifted to today. If saved forecasts expire, the overview shows current predictions as unavailable while historical analysis and the simulator remain usable. Snapshot refresh is an explicit maintenance command; the app never overwrites committed files.

### Decision Framework

Illustrative afternoon-mean tiers: Good <50; Moderate 50–<60; High 60–<70; Very High ≥70 ppb, configurable in `src/config.py`. Public-health messaging, hospital capacity, school activities, outdoor work, city operations and pharmacy stock each have an accountable decision-maker and success measure.

The [2025 Canadian CAAQS](https://ccme.ca/en/air-quality-report) ozone standard is 60 ppb; [US EPA NAAQS](https://www.epa.gov/ground-level-ozone-pollution/ozone-national-ambient-air-quality-standards-naaqs) is 70 ppb. Both are based on the three-year average of the annual fourth-highest daily maximum eight-hour average. The dashboard target and tiers do not establish compliance or replace official AQHI guidance.

Prioritise recall during screening design because missed events can harm vulnerable groups; weigh false-alarm fatigue and operational cost with partners. The slider explores held-out behaviour, not an independently validated choice of policy. False-alarm rate means FP/(FP+TN); zero denominators remain missing. No health outcome data are used to quantify benefit.

### Architecture

```mermaid
flowchart LR
    A[Open-Meteo and ECCC] --> B[Retried cached API clients]
    S[Timestamped sample JSON] --> B
    B --> C[DST-aware hourly to daily transforms]
    C --> D[Past-only OLS and chronological holdout]
    D --> E[Decision metrics and Plotly]
    E --> F[Seven Streamlit pages]
    R[R airquality 1973] --> M[Separate method baseline]
    M --> F
```

`app/` owns navigation and page scripts; `src/` owns configuration, API, transforms, models, decisions and charts. `tests/fixtures/` holds real JSON fixtures. `scripts/` refreshes snapshots, verifies live behaviour and generates README findings. `notebooks/analysis.ipynb` reproduces the baseline; `docs/` contains evidence and the screenshot.

`powerbi/` holds the native PBIP project, PBIR report pages, TMSL semantic model, DAX measures and CSV evidence. Rebuild with `python scripts/build_powerbi.py`; validate native JSON with `python scripts/validate_powerbi.py`. Power BI's in-app Refresh reloads the embedded snapshot, while new API data and retraining require the documented Python refresh/rebuild workflow.

### Run Locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Choose a city and page in the sidebar. Use **Use saved API snapshots** for deterministic offline exploration. `AIR_QUALITY_OFFLINE=1` also disables API calls. Set it before starting Streamlit. Refresh cached calls with the sidebar button. The Windows development environment blocked a newer PyArrow DLL; a compatible PyArrow 19 series is pinned, and targeted statsmodels imports avoid loading unused state-space binaries. Local verification used the bundled Python 3.12 runtime; CI targets the requested Python 3.11.

```bash
python scripts/snapshot.py --refresh-all # explicitly refresh real-source JSON
python scripts/build_docs.py     # regenerate findings and daily CSVs
python scripts/verify_live.py    # opt-in network integration test
```

### Deploy On Streamlit Community Cloud

To publish the optional live Python app, create an app in Streamlit Community Cloud from this GitHub repository. Set the entry point to `app/streamlit_app.py` and select Python 3.11 in advanced settings. Deploy, verify source timestamps, then replace the live-link placeholder above. Core functionality requires no API key. The Power BI Desktop report can be opened locally independently of Streamlit.

### Testing

```bash
pytest -q
ruff check .
```

Default tests need no internet: source JSON mocks cover every API, including outage fallback; known-value tests cover conversion, daily energy, missing-hour gates, DST, model fitting, chronological isolation and alert boundaries. Streamlit AppTest executes every page and the entry point with APIs disabled. `scripts/verify_live.py` checks live retrieval for all configured Ontario locations, every page and entry routing; its dated evidence is saved in `docs/live_verification.json`. CI runs pytest and ruff on pushes and PRs. Local results are recorded in `docs/verification.md`.

### Limitations and Next Steps

Correlation is not causation. Omitted emissions, traffic, humidity and transport, modelled ozone, short seasonal training windows, missingness, serial dependence and weather forecast error limit operational use. An interval conditional on OLS assumptions is not a calibrated health-risk bound. Training R² is not an alert-readiness measure.

Next: station-level ECCC validation, rolling-origin forecast evaluation, governed ER-outcome linkage, SARIMAX and gradient-boosting comparisons, calibrated alerts and opt-in notifications. Check official AQHI and local public-health advice for real health decisions.
