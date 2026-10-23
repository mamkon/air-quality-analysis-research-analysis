"""Operational choices and alert trade-offs."""
import pandas as pd
import plotly.express as px
import streamlit as st

from src.bootstrap import require_context
from src.config import TIERS
from src.decisions import confusion, matrix
from src.modeling import metrics, vif
from src.viz import theme

require_context("framework.py")
ctx = st.session_state.ctx
st.title("From prediction to a decision")
tier_text = []
lower = 0
for upper, label, _ in TIERS:
    interval = f"{lower:g}–<{upper:g}" if upper != float("inf") else f"≥{lower:g}"
    tier_text.append(f"{label}: {interval} ppb")
    lower = upper
st.write("Illustrative afternoon-mean tiers: " + "; ".join(tier_text) + ". "
         "The Canada CAAQS 2025 ozone standard is 60 ppb; the US EPA NAAQS is 70 ppb. Both use the "
         "three-year average of the annual fourth-highest daily maximum eight-hour concentration. "
         "These are not comparable compliance measurements or official health-advisory thresholds.")
st.markdown("[CCME standard](https://ccme.ca/en/air-quality-report) · [EPA standard](https://www.epa.gov/ground-level-ozone-pollution/ozone-national-ambient-air-quality-standards-naaqs)")
st.dataframe(matrix(), hide_index=True, width="stretch")
cutoff = st.slider("High-ozone cutoff (ppb)", 20, max(100, int(TIERS[1][0])), int(TIERS[1][0]))
evaluation = ctx["evaluation"]
scores = confusion(evaluation.ozone, evaluation.predicted, cutoff)
grid = [[scores["TN"], scores["FP"]], [scores["FN"], scores["TP"]]]
fig = px.imshow(grid, x=["No alert", "Alert"], y=["Below cutoff", "At/above cutoff"], text_auto=True, color_continuous_scale="Blues")
st.plotly_chart(theme(fig, "Chronological held-out confusion matrix", "Predicted class", "CAMS reference class"), width="stretch")
st.caption("Takeaway: zero event support means recall is unknown, not evidence of a safe model.")
st.dataframe(pd.DataFrame([{k: v for k, v in scores.items() if k not in ["TP", "TN", "FP", "FN"]}]))
st.write(f"Evaluation support: {scores['TP'] + scores['FN']} event days; {scores['TN'] + scores['FP']} non-event days. "
         "False-alarm rate here means FP/(FP+TN), rather than the share of alerts that were false.")
st.info("Prefer recall when designing a public-health screening workflow because missed days can harm vulnerable groups. "
        "False alarms create alert fatigue and staffing costs. Select thresholds with public-health partners using a separate tuning window; "
        "this exploratory slider is not a validated policy recommendation.")
st.subheader("Analytical decision trail")
st.dataframe(pd.DataFrame([
    {"Step": "Align", "Decision": "Exclude incomplete local days", "Evidence": f"{len(ctx['past'])} complete past days", "Impact": "No partial-day target leakage"},
    {"Step": "Fit", "Decision": "OLS with temperature, wind, radiation", "Evidence": f"Adjusted R²={ctx['model'].rsquared_adj:.3f}", "Impact": "Interpretable associations"},
    {"Step": "Diagnose", "Decision": "Inspect residual normality", "Evidence": f"Shapiro p={metrics(ctx['model'])['Residual Shapiro p']:.4g}", "Impact": "Qualify prediction-interval assumptions"},
    {"Step": "Collinearity", "Decision": "Inspect predictor overlap", "Evidence": f"Maximum VIF={vif(ctx['past']).VIF.max():.2f}", "Impact": "Avoid overinterpreting unstable coefficients"},
    {"Step": "Validate", "Decision": "Latest quarter held out", "Evidence": f"n={len(evaluation)}", "Impact": "Chronological generalisation check"},
    {"Step": "Decide", "Decision": "Inspect recall and support", "Evidence": f"Recall={scores['Recall']:.3f}", "Impact": "Explicit missed-event trade-off"},
]), hide_index=True)

