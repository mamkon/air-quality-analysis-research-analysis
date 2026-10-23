"""Historical baseline, missingness and regression diagnostics."""
import numpy as np
import pandas as pd
import streamlit as st

from src import api_clients, viz
from src.bootstrap import require_context
from src.modeling import (
    baseline_frame,
    baseline_sensitivity,
    fit,
    metrics,
    missing_comparison,
    normality,
    vif,
)

require_context("method.py")
st.title("Background & Method")
st.warning("1973 data, used to demonstrate method only.")
st.write("Sunlight drives reactions between nitrogen oxides and volatile organic compounds, forming ground-level ozone. "
         "Ozone irritates the respiratory system and aggravates asthma; children, older adults and people with respiratory disease need particular attention. "
         "Respiratory emergency visits are a relevant future outcome, not a measured outcome in this project.")
st.markdown("[Health Canada / ECCC context](https://www.canada.ca/en/environment-climate-change/services/environmental-indicators/air-quality.html)")
source = api_clients.baseline(st.session_state.ctx["offline"])
if source.attrs.get("cached"):
    st.warning(f"Baseline: Showing cached data from {source.attrs.get('retrieved_at')}. Canonical R airquality data (1973).")
st.caption(f"Baseline retrieval: {source.attrs.get('retrieved_at')} · R datasets / airquality.")
raw = baseline_frame(source)
clean = raw.dropna()
st.dataframe(missing_comparison(raw), hide_index=True)
st.write(f"Use complete cases (n = {len(clean)}): mean/median filling suppresses variability and can distort associations. "
         "Complete cases also risk selection bias if missingness is informative.")
with st.expander("How missing-data choices change the regression"):
    sensitivity = baseline_sensitivity(raw)
    st.dataframe(sensitivity, hide_index=True)
    complete, mean = sensitivity.iloc[0], sensitivity.iloc[1]
    st.write(f"Mean imputation fits {int(mean['n'])} rows, including {int(mean['Imputed ozone targets'])} "
             f"filled ozone responses, with R² = {mean['R²']:.3f}. The primary complete-case model "
             f"uses {int(complete['n'])} observed rows with R² = {complete['R²']:.3f}. "
             "These differ because preprocessing changes both the sample and response variability; "
             "higher training R² across these samples does not establish better predictive performance. "
             "Imputed ozone values are never used as live-model validation targets.")
    st.download_button("Download baseline sensitivity results", sensitivity.to_csv(index=False),
                       "baseline_sensitivity.csv", "text/csv")
st.caption("Baseline units: ozone ppb, temperature °F, wind mph, solar Langleys (narrow spectral band). No conversion to modern broadband radiation is assumed.")
variable = st.selectbox("Inspect baseline variable", list(clean))
units = {"ozone": "Ozone (ppb)", "temp": "Temperature (°F)", "wind": "Wind (mph)", "solar": "Solar (Langleys)"}
left, right = st.columns(2)
left.plotly_chart(viz.histogram(clean[variable], units[variable]), width="stretch")
right.plotly_chart(viz.qq(clean[variable], units[variable]), width="stretch")
st.caption("Takeaway: assess skew and tail departures visually; OLS inference concerns residuals rather than normal predictors.")
st.dataframe(normality(clean), hide_index=True)
st.caption("A small Shapiro p-value suggests departures from normality. A large p-value means insufficient evidence to reject normality; it does not prove a normal distribution.")
left, right = st.columns(2)
left.plotly_chart(viz.heatmap(clean, "pearson"), width="stretch")
right.plotly_chart(viz.heatmap(clean, "spearman"), width="stretch")
st.caption("Takeaway: Pearson measures linear association; Spearman uses ranks for monotonic relationships and is less sensitive to extremes.")
simple, multiple, log_model = fit(clean, ["temp"]), fit(clean), fit(clean, log=True)
st.subheader("Regression comparisons")
results = pd.DataFrame([metrics(m) for m in [simple, multiple, log_model]], index=["Simple", "Multiple", "Log response"])
st.dataframe(results)
st.caption("Log-response RMSE is in log(ppb). Its R², AIC and BIC cannot be directly compared with raw-response models; a response transformation changes the likelihood scale.")
for name, model in [("Simple OLS", simple), ("Multiple OLS", multiple)]:
    st.write(f"**{name}**")
    st.dataframe(pd.DataFrame({"Coefficient": model.params, "p": model.pvalues,
                               "95% lower": model.conf_int()[0], "95% upper": model.conf_int()[1]}))
st.write(f"Holding solar and wind fixed, a one °F increase in temperature is associated with {multiple.params['temp']:.2f} ppb ozone. This is an association, not a causal effect.")
st.write(f"In simple OLS, the temperature association is {simple.params['temp']:.2f} ppb per °F "
         f"(R² = {simple.rsquared:.3f}). In multiple OLS, holding other predictors fixed, "
         f"wind has an association of {multiple.params['wind']:.2f} ppb per mph and "
         f"solar radiation {multiple.params['solar']:.3f} ppb per Langley. "
         "Coefficient p-values describe conditional evidence under model assumptions, not causal importance.")
st.plotly_chart(viz.residual(multiple), width="stretch")
st.caption("Takeaway: curvature or changing residual spread weakens a linear model's uncertainty assumptions.")
st.plotly_chart(viz.qq(pd.Series(log_model.resid, name="log-model residual"), "Residual (log ppb)"), width="stretch")
st.caption("Takeaway: the log model is a sensitivity analysis for skew and residual behaviour.")
st.dataframe(vif(clean), hide_index=True)
st.caption(f"Baseline log-model geometric residual factor: {np.exp(log_model.resid.std()):.2f}; not a retransformed prediction interval.")

