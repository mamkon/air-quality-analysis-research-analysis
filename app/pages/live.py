"""Modern fit and chronological validation."""
import numpy as np
import pandas as pd
import streamlit as st

from src import api_clients, viz
from src.bootstrap import require_context
from src.modeling import baseline_frame, fit, metrics, vif

require_context("live.py")
ctx = st.session_state.ctx
st.title(f"Live Ontario Model · {ctx['city']}")
past, evaluation, model = ctx["past"], ctx["evaluation"], ctx["model"]
st.write(f"Training window: {past.index.min().date()} to {past.index.max().date()} · {len(past)} complete days. "
         "The latest quarter is held out chronologically for validation; the deployment model is then refit on all past days.")
base = fit(baseline_frame(api_clients.baseline(ctx["offline"])).dropna())
st.dataframe(pd.DataFrame([metrics(base), metrics(model)], index=["NYC 1973 (original units)", f"Ontario {past.index.max().year} (SI units)"]))
rmse = float(np.sqrt(np.mean(evaluation.residual**2)))
st.metric("Held-out RMSE", f"{rmse:.2f} ppb")
st.plotly_chart(viz.lines(evaluation, ["ozone", "predicted"], "Held-out CAMS reference vs OLS prediction", "Afternoon ozone (ppb)"), width="stretch")
st.caption("Takeaway: all displayed validation predictions use only earlier training days. CAMS reference values are modelled, not station observations.")
st.plotly_chart(viz.residual(model), width="stretch")
st.caption("Takeaway: inspect patterns that suggest missing seasonality, nonlinearities or unequal variance.")
st.plotly_chart(viz.lines(evaluation, ["rolling_rmse"], "Rolling validation error · seven days", "RMSE (ppb)"), width="stretch")
st.caption("Takeaway: error changes over time; the first incomplete rolling windows are omitted.")
st.dataframe(vif(past), hide_index=True)
st.dataframe(pd.DataFrame({"Coefficient": model.params, "p": model.pvalues}))
st.write(f"The modern adjusted R² is {model.rsquared_adj:.3f}, compared with {base.rsquared_adj:.3f} in the baseline. "
         "Different seasons, geography, emissions controls and source systems could explain differences; this comparison cannot isolate their effects. "
         "Historical reanalysis weather validation is retrospective and can overstate operational forecast skill.")
if model.rsquared < 0.05 or model.rsquared > 0.95:
    st.warning("Fit is near a boundary. Check source variation, alignment and predictive usefulness before operational use.")
st.download_button("Download aligned daily data", past.to_csv(), "daily_model_data.csv", "text/csv")

