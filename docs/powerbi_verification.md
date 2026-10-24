# Native Power BI Verification

## Desktop Checks

Verified on 24 October 2026 in the installed Power BI Desktop:

- All eight editable pages render with the imported data.
- The standalone AIR QUALITY ANALYSIS RESEARCH ANALYSIS.pbix was saved by Desktop, closed and reopened. Toronto's overview returns the same values without localhost or an Excel connection.
- The file contains an embedded DataModel, eight report pages and 83 native visuals. ZIP integrity checks pass.
- Changing the overview from Toronto to Barrie changes the chart and KPIs. Kenora retains a blank official AQHI, with unavailable local context shown in the source table.
- The alert cutoff changes confusion counts and rates. At Toronto's 26 ppb test cutoff, the matrix shows 21 true positives and two false negatives; recall is 91.3%. Restoring the default calculation returns zero event days at 60 ppb, with undefined precision and recall left blank.
- Changing the weather preset from Typical summer day to Hot, calm, sunny changes Toronto's illustrative prediction from 49.23 to 65.20 ppb and flags the latter as outside the training range. The typical preset was restored before saving.
- Historical model comparison, correlations, coefficients and normality results display. Very small p-values use scientific notation.

## Repairs

The generated internal report version was changed from 4.0.0 to the 2.0.0 version saved by this Desktop installation. The separate definition.pbir version remains 4.0. Native theme metadata and its resource were retained. The slicer defaults now set a selection, rather than restricting the list of choices. A text encoding defect affecting accented symbols and a historical field reference was repaired.

## Automated Checks and Limits

- 85 core and Power BI tests pass locally, including exact scenario prediction-limit parity with Python OLS for Toronto, Ottawa and Kenora.
- Ruff passes. A regression test covers the internal format and Toronto slicer defaults.
- The complete local Streamlit page-test run was attempted but did not finish in this Windows session. It is not claimed as passing for this revision. GitHub Actions runs the full suite on Python 3.11.
- Earlier definitions passed their official JSON schemas; the decisive new check is the native Desktop rendering and PBIX reopen test.
- These checks establish report operation, not year-round forecasting accuracy or clinical validity.

## Data Meaning

The file is a dated research snapshot from sources retrieved on 23 October 2026. It covers 47 selected Ontario locations, not every community or a complete station network. CAMS ozone is modelled reference data, not station observations. Missing local official AQHI is never replaced with another city's value. Power BI Refresh reloads the embedded snapshot; new API data and retraining require the documented Python workflow. The Python/Streamlit application is the live API version.

## Ontario Map Checks

Added on 24 October 2026 as the first page, preserving the existing seven pages. The standalone map copy contains eight pages, 83 visuals and an embedded DataModel; ZIP integrity checks pass.

Azure Maps rendered the reviewed Ontario coordinates. Eastern Ontario filtered to five locations and clearing the filter restored all regions. Fort Severn showed 30.61 ppb with source time 23 October 2026 at 00:00 Eastern time; selecting and clearing its bubble updated the adjacent table. Missing official AQHI stayed blank. The saved default is All regions. Bubbles use dark blue on a grey basemap with 4–12 pixel radii, plus a table alternative. Map tiles need internet access. The source snapshot was not refreshed or retrained.
