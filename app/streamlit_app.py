"""Streamlit entry point; run from repository root."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402

from src.config import AUTHOR, LOCATION_DETAILS, LOCATIONS, REGIONS  # noqa: E402
from src.context import load  # noqa: E402

st.set_page_config(page_title="Ontario Ozone · Decision Observatory", page_icon="◉", layout="wide")
st.markdown("""<style>
.stApp {background:#f7fafb;} h1,h2,h3 {color:#15394b;}
[data-testid="stMetric"] {background:white;border:1px solid #dce6eb;border-radius:12px;padding:18px;}
[data-testid="stSidebar"] {background:#eaf1f4;}
.block-container {padding-top:4.5rem;max-width:1450px;}
</style>""", unsafe_allow_html=True)
st.sidebar.markdown("## ◉ Ontario Ozone\nDecision Observatory")
region = st.sidebar.selectbox("Ontario region", ["All Ontario", *REGIONS], key="region")
choices = [city for city in LOCATIONS if region == "All Ontario" or LOCATION_DETAILS[city]["region"] == region]
if st.session_state.get("city") not in choices:
    st.session_state["city"] = choices[0]
city = st.sidebar.selectbox("Location", choices, key="city")
st.sidebar.caption(f"{len(LOCATIONS)} locations across Ontario · local time: {LOCATION_DETAILS[city]['timezone']}")
offline = st.sidebar.toggle("Use saved API snapshots", value=False)
if st.sidebar.button("Refresh sources"):
    st.cache_data.clear()
st.sidebar.caption(AUTHOR)
st.sidebar.caption("Data Analytics & Business Intelligence Consultant")
st.sidebar.info("Planning illustration. Follow official ECCC AQHI and local public-health guidance.")
pages = [("overview.py", "Overview"), ("method.py", "Background & Method"),
         ("live.py", "Live Ontario Model"), ("framework.py", "Decision Framework"),
         ("simulator.py", "What-If Simulator"), ("audience.py", "Who Uses This"),
         ("limitations.py", "Limitations & Next Steps")]
page = st.navigation([st.Page(f"pages/{file}", title=title) for file, title in pages])
st.caption("ENVIRONMENTAL INTELLIGENCE")
try:
    with st.spinner("Aligning weather and air-quality sources…"):
        st.session_state.ctx = load(city, offline)
except (ValueError, KeyError, TypeError) as exc:
    st.error(f"Model unavailable: {exc}. Try saved snapshots or refresh sources.")
    st.stop()
ctx = st.session_state.ctx
for name, envelope in ctx["sources"].items():
    if envelope["cached"]:
        st.warning(f"{name}: Showing cached data from {envelope['retrieved_at'] or 'unavailable'}. "
                   f"{envelope.get('error', '')}")
bootstrap_page = st.session_state.pop("_bootstrap_page", None)
if bootstrap_page in {file for file, _ in pages}:
    st.switch_page(f"pages/{bootstrap_page}")
page.run()
st.divider()
st.caption(f"Last updated (render): {ctx['now'].isoformat()} · Dates use the selected location's time zone: {ctx['timezone']}.")
with st.expander("Source attribution and retrieval timestamps"):
    for name, source in ctx["sources"].items():
        st.caption(f"{name}: {source['retrieved_at']} · {source['source']}")
    st.caption("Open-Meteo / CAMS (Copernicus Atmosphere Monitoring Service), CC BY 4.0; "
               "ECCC MSC GeoMet, Open Government Licence – Canada; R datasets / airquality.")

