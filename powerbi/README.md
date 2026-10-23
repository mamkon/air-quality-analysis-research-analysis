# AIR QUALITY ANALYSIS RESEARCH ANALYSIS — Power BI Desktop

Open **AIR QUALITY ANALYSIS RESEARCH ANALYSIS.pbip** in current Power BI Desktop.
Keep its adjacent `.Report` and `.SemanticModel` folders together. If data have
not yet been imported, select **Home → Refresh**. You can then use **File → Save
As** to save a standalone `.pbix` copy.

This is a native, editable Power BI report with seven pages, 23 import tables,
relationships, Ontario location filters and 40 DAX measures. It is not a screenshot
or an embedded web dashboard. The source project uses Microsoft's PBIR/TMSL
formats, which support version control in GitHub.

**Current verification:** the native definition schemas and OLS scenario arithmetic
pass validation, but this environment's Desktop application stayed blank while
opening the project. Native rendering and a standalone `.pbix` are not yet verified.
See `docs/powerbi_verification.md` in the repository.

## Pages

1. **Overview:** dated ozone/forecast/AQHI/fit KPIs, prediction bounds and source age.
2. **Historical Method:** separate NYC 1973 baseline, missing-data comparison,
   simple/multiple/log OLS, correlations, Shapiro tests and coefficients.
3. **Ontario Model:** chronological validation, residuals and rolling RMSE.
4. **Decision Framework:** cutoff selector, confusion matrix, precision/recall,
   false-alarm/missed-event rates, event support and accountable actions.
5. **What-If Simulator:** presets plus optional weather overrides, native DAX
   prediction limits using the fitted coefficient covariance, and extrapolation checks.
6. **Who Uses This:** industries, decisions, illustrative employers and role evidence.
7. **Limitations:** statistical limitations and original per-location source timestamps.

Choose one location. Clear the location selection before changing a region if
the current location is outside that region. The selectors are native Power BI
slicers; their selections can be cleared with the eraser icon. In the simulator,
clear a manual weather override to return to the selected preset.

## Data freshness and refresh

**Power BI is a dated research snapshot.** It imports genuine source data from
`data/sample` through the existing Python pipeline. It does not call the live
Streamlit server or require it to remain running. Embedded compressed import
partitions make the project portable and avoid user-specific paths or credentials.
The CSV exports in `powerbi/data/` provide transparent evidence of every imported table.

To update the snapshot, close this Power BI project, then run from the repository root:

```bash
python scripts/snapshot.py --refresh-all
python scripts/build_docs.py
python scripts/build_powerbi.py
```

Reopen the `.pbip` and select **Refresh**. Re-save any standalone `.pbix` after
refreshing. Power BI's Refresh button alone reloads the currently embedded snapshot;
it does not download new source observations or retrain OLS. The Streamlit app
remains the live API version. No paid Power BI cloud service is needed to open
the Desktop report.

Do not rebuild a project that has unsaved edits in Power BI Desktop. The generator
owns the project definition files; retain custom report edits in a separate copy.

## Measurement and model discipline

- 47 Ontario points across six regions, with exact local ECCC AQHI identity for
  41 configured official areas. Missing official context is blank, never another city.
- Each modern location has its own model; the 1973 model never scores modern inputs.
- Native what-if DAX uses max temperature °C, mean wind km/h and full-day mean
  radiation W/m² integrated with ×0.0864 into MJ/m²/day.
- The 95% scenario interval is `prediction ± t × residual_sigma × sqrt(1+x' inv(X'X) x)`.
  It is conditional on OLS assumptions and excludes forecast/CAMS uncertainty.
- Event metrics use chronological holdout predictions. Unsupported ratios remain
  blank. A blank recall must not be interpreted as zero missed events.
- Log-response model statistics use a different scale and cannot be directly
  ranked against raw-response AIC/BIC, RMSE or R².
- Afternoon ozone mean is not an eight-hour standard or an official health advisory.

## Technical files and verification

`measures.dax` exposes the native calculations. `data/manifest.json` records table
counts and build time. `scripts/validate_powerbi.py` validates PBIR documents against
Microsoft's public JSON schemas; Desktop loading checks DAX/M and visual rendering.

Official format references: [PBIP overview](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview),
[report folder](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report),
[semantic model folder](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset).

Author: Mercy Mamkon Oyeleke, Data Analytics & Business Intelligence Consultant.
