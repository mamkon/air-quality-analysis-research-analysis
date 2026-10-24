"""Recruiter-facing evidence of transferable analytical skills."""
from pathlib import Path

import pandas as pd
import streamlit as st

from src.bootstrap import require_context

require_context("audience.py")
st.title("Who uses air-quality data, and why?")
st.write("A decision-oriented portfolio by Mercy Mamkon Oyeleke, Data Analytics & Business Intelligence Consultant.")
st.markdown((Path(__file__).resolve().parents[2] / "docs" / "plain_language_guide.md").read_text(encoding="utf-8-sig"))
st.subheader("Examples of related jobs")
rows = [
    ("Public health", "Advisory preparation", "Toronto Public Health; Public Health Ontario", "Epidemiology / health data analyst", "Decision Framework"),
    ("Hospitals", "Respiratory capacity planning", "UHN; Unity Health Toronto", "Clinical / BI analyst", "Overview"),
    ("Government / environment", "Environmental monitoring", "ECCC; Ontario MECP", "Environmental data analyst", "Live Ontario Model"),
    ("ESG consulting", "Exposure reporting", "Deloitte; WSP", "Sustainability analyst", "Background & Method"),
    ("Insurance", "Environmental risk screening", "Intact; Manulife", "Risk analyst", "Limitations & Next Steps"),
    ("Energy / utilities", "Weather-linked operations", "Hydro One; Toronto Hydro", "Operations analyst", "What-If Simulator"),
    ("Urban planning / transit", "Outdoor exposure planning", "City of Toronto; Metrolinx", "Planning / transport analyst", "Decision Framework"),
    ("Pharma / pharmacy", "Demand preparedness", "Shoppers Drug Mart; McKesson Canada", "Supply-chain / commercial analyst", "Overview"),
]
st.dataframe(pd.DataFrame(rows, columns=["Industry", "Decision supported", "Illustrative employers (not endorsements or openings)", "Job titles", "Page proving skill"]), hide_index=True, width="stretch")

