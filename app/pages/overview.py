"""Executive view."""
import pandas as pd
import streamlit as st

from src import viz
from src.bootstrap import require_context
from src.config import LOCATION_DETAILS, LOCATIONS
from src.context import aqhi_table
from src.decisions import action, risk
from src.modeling import predict

require_context("overview.py")
ctx = st.session_state.ctx
st.title("Cleaner signals. Earlier decisions.")
st.write(f"Weather-based ozone planning for **{ctx['city']}, Ontario** · {LOCATION_DETAILS[ctx['city']]['region']}.")
available = ctx["ozone_hourly"].loc[lambda f: f.index <= ctx["now"]].dropna()
current = available.iloc[-1].ozone / 1.96 if len(available) else float("nan")
forecast = predict(ctx["model"], ctx["future"]) if len(ctx["future"]) else pd.DataFrame()
today = forecast.predicted.iloc[0] if len(forecast) and forecast.index[0].date() == ctx["now"].date() else float("nan")
tier = risk(today)
table = aqhi_table(ctx["sources"]["Local AQHI observations"])
if len(table) and "observation_datetime" in table:
    table = table.sort_values("observation_datetime")
aqhi = table.iloc[-1].get("aqhi", "Unavailable") if len(table) else "Unavailable"
cols = st.columns(5)
for col, label, value in zip(cols, ["Latest CAMS ozone", "Today's prediction", "Illustrative tier", "Local ECCC AQHI", "Model adjusted R²"],
    [f"{current:.1f} ppb" if pd.notna(current) else "Unavailable",
     f"{today:.1f} ppb" if pd.notna(today) else "Unavailable", tier, str(aqhi), f"{ctx['model'].rsquared_adj:.3f}"]):
    col.metric(label, value)
st.subheader(f"Today in {ctx['city']}: {tier}")
st.write(f"Recommended actions: {action(tier)}")
if len(available):
    st.caption(f"Latest CAMS value timestamp: {available.index[-1].isoformat()}; modelled, not a station reading.")
    if (ctx["now"] - available.index[-1]).total_seconds() > 3 * 3600:
        st.warning("Latest CAMS value is stale; check the displayed observation timestamp.")
if len(table):
    latest = table.iloc[-1]
    st.caption(f"AQHI location: {latest.get('location_name_en', ctx['city'])} · observation: {latest.get('observation_datetime', 'unknown')}")
    observed_at = pd.to_datetime(latest.get("observation_datetime"), utc=True)
    if pd.notna(observed_at) and (ctx["now"] - observed_at).total_seconds() > 3 * 3600:
        st.warning("Official AQHI observation is older than three hours; consult ECCC for current advice.")
else:
    st.info("Official AQHI is unavailable for this selected location. No other city's AQHI has been substituted. Check ECCC for regional health guidance.")
if len(forecast):
    st.plotly_chart(viz.forecast(forecast), width="stretch")
    st.caption(f"Takeaway: {len(forecast)} complete forecast days; the band represents OLS uncertainty and excludes weather-forecast uncertainty.")
else:
    st.info("Saved forecast dates are historical. Current predictions are unavailable; view the historical model or simulator.")
st.info("AQHI combines multiple pollutants. It is separate from this dashboard's afternoon ozone tiers.")
with st.expander(f"Official AQHI observations and forecasts · {ctx['city']}"):
    st.dataframe(table, hide_index=True)
    st.dataframe(aqhi_table(ctx["sources"]["Local AQHI forecasts"]), hide_index=True)
with st.expander("Ontario coverage · locations and official AQHI availability"):
    coverage = pd.DataFrame([{"Location": name, "Region": details["region"],
        "lat": details["latitude"], "lon": details["longitude"],
        "Official AQHI": "Available area" if details["aqhi_id"] else "No configured official area",
        "Time zone": details["timezone"]} for name, details in LOCATION_DETAILS.items()])
    st.map(coverage, latitude="lat", longitude="lon", zoom=4)
    st.caption(f"{len(LOCATIONS)} selectable locations across Ontario. Point estimates are not continuous station coverage of every community.")
    st.dataframe(coverage.drop(columns=["lat", "lon"]), hide_index=True, width="stretch")

