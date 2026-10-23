"""Boundaries of interpretation and a practical roadmap."""
import streamlit as st

from src.bootstrap import require_context

require_context("limitations.py")
st.title("Honest boundaries. Clear next steps.")
st.markdown("""
- **Association is not causation.** Emissions, traffic, humidity, transport and atmospheric chemistry are omitted.
- **CAMS is modelled reference data.** Agreement with another model does not establish agreement with ground stations or health outcomes.
- **Short and seasonal training window.** A recent window cannot establish year-round performance or behaviour during rare events.
- **Retrospective weather.** Archive weather is reanalysis, while deployment uses forecasts; measured operational skill needs archived forecast vintages.
- **Unit assumption.** Ozone ppb = µg/m³ ÷ 1.96 at 25 °C and 1 atm. Real atmospheric conditions vary.
- **Different endpoints.** Afternoon ozone mean is not an eight-hour maximum; AQHI is a separate multi-pollutant index.
- **Uncertainty assumptions.** OLS intervals assume an adequate linear specification and independent, constant-variance residuals. They exclude weather and CAMS model uncertainty.
- **Missingness and stale data.** Complete cases can bias the sample. Cached dates are preserved and never relabelled as current observations.
- **Ontario coverage.** Selectable community and monitoring-area points do not cover every address. ECCC AQHI is unavailable for some northern communities; no other city's value is substituted. Model grid cells and official AQHI areas may have different spatial supports.
- **Temporal dependence and selection.** A single chronological split is a starting point; threshold exploration is not independent policy validation.
""")
st.subheader("Next steps")
st.write("Validate against station-level ECCC ozone; evaluate rolling-origin forecasting with archived weather forecasts; "
         "link appropriately governed respiratory ER outcomes; compare SARIMAX and gradient boosting; "
         "calibrate intervals and alerts with public-health partners before adding opt-in notifications.")
st.link_button("Official Canadian AQHI", "https://weather.gc.ca/airquality/pages/index_e.html")

