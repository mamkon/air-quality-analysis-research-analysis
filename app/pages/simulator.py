"""Scenario inputs use the modern model's daily weather definitions."""
import pandas as pd
import streamlit as st

from src.bootstrap import require_context
from src.decisions import action, risk
from src.modeling import predict
from src.viz import forecast

require_context("simulator.py")
ctx = st.session_state.ctx
st.title("What if the weather changes?")
st.caption("Illustrative, not a health advisory. Uses the selected city's modern model.")
presets = {"Hot, calm, sunny": (33, 5, 300), "Cool and windy": (17, 25, 140), "Typical summer day": (26, 13, 230)}
scenario = st.selectbox("Preset scenario", list(presets))
t, w, s = presets[scenario]
temp = st.slider("Daily maximum temperature (°C)", -15, 45, t, key=f"t_{scenario}")
wind = st.slider("Daily mean wind (km/h)", 0, 60, w, key=f"w_{scenario}")
solar = st.slider("Full-day mean shortwave radiation (W/m²)", 0, 450, s, key=f"s_{scenario}")
row = pd.DataFrame({"temp": [temp], "wind": [wind], "solar": [solar * 86400 / 1e6]}, index=[ctx["now"].normalize()])
prediction = predict(ctx["model"], row)
p = prediction.iloc[0]
tier = risk(p.predicted)
st.metric("Predicted afternoon ozone", f"{p.predicted:.1f} ppb")
st.write(f"95% prediction interval: {p.lower:.1f} to {p.upper:.1f} ppb · {tier}. {action(tier)}")
st.plotly_chart(forecast(prediction), width="stretch")
st.caption(f"Takeaway: full-day mean radiation is integrated to {row.solar.iloc[0]:.2f} MJ/m²/day before scoring; it is not an instantaneous noon measurement.")
for feature in row:
    low, high = ctx["past"][feature].min(), ctx["past"][feature].max()
    if not low <= row[feature].iloc[0] <= high:
        st.warning(f"{feature} is outside the training range [{low:.2f}, {high:.2f}]. This is extrapolation.")
if p.lower < 0:
    st.caption("OLS can produce physically impossible negative lower bounds; intervals are shown raw to expose this limitation.")

