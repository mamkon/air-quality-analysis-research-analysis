# Working on Ontario Ozone

Run `pip install -r requirements.txt`, then `streamlit run app/streamlit_app.py`
from the repository root. Python 3.11 is the deployment target. Run `pytest -q`
and `ruff check .` before committing. CI repeats both on Python 3.11.

`src/config.py` owns URLs, locations, thresholds and cache TTLs. `api_clients.py`
owns retried HTTP and explicit fallback envelopes. `transform.py` owns units and
DST-safe local daily alignment. `modeling.py` owns OLS and chronological validation.
`decisions.py` owns alert policy; `viz.py` owns Plotly styling. `context.py` assembles
sources for the seven scripts in `app/pages/`.
`data/ontario_locations.json` holds reviewed provincial locations, regions, local
time zones and exact ECCC AQHI area IDs. Never substitute Toronto AQHI for a
different location or use Eastern time for Western Ontario points in Central time.
The metadata refresh script uses official station and geocoding sources.

Keep functions documented and typed. Never fabricate source snapshots, shift their
dates, treat CAMS as station observations, score modern data with the historical
model, or use future targets in training. Keep log-scale statistics separate from
raw-scale comparisons. Preserve unknown metrics as missing when unsupported.
Every page inherits provenance and retrieval times from the entry point.
Call `bootstrap.require_context` at the top of each page so a fresh legacy
pages-directory deep link initializes through the entry point before rendering.
Historical mean/median model sensitivity may fill missing responses only for
descriptive comparison; live validation must retain observed/modelled source targets.

Refresh real snapshots explicitly with `python scripts/snapshot.py --refresh-all`.
Without that flag the command resumes missing snapshots. The app never
overwrites committed snapshots. API JSON envelopes contain retrieval timestamps;
`data/sample/daily_*.csv` are derived convenience snapshots. Test fixtures use saved
source JSON; network access must not be needed for default tests. Use the sidebar
snapshot switch or `AIR_QUALITY_OFFLINE=1` to test complete API failure.

Make small commits around coherent changes. Do not publish credentials or claim
this dashboard is a validated advisory system.
