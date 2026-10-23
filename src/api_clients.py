"""Retried HTTP clients with immutable, timestamped offline snapshots."""
import json
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pandas as pd
import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import (
    ARCHIVE_URL,
    ECCC_URL,
    FORECAST_URL,
    HISTORICAL_TTL,
    LIVE_TTL,
    LOCATION_DETAILS,
    LOCATIONS,
    OZONE_URL,
    SAMPLE,
    TIMEOUT,
    WEATHER,
)


def request_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    """GET JSON with bounded retries, status checks and timeout."""
    with requests.Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=Retry(
            total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])))
        response = session.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()


def fetch(url: str, params: dict[str, Any], key: str, offline: bool = False) -> dict:
    """Return a validated payload envelope or the exact saved source snapshot."""
    try:
        if offline or os.getenv("AIR_QUALITY_OFFLINE") == "1":
            raise requests.ConnectionError("API disabled")
        payload = request_json(url, params)
        if "hourly" in payload:
            hourly = payload["hourly"]
            if not hourly.get("time") or not any(
                value is not None for field in hourly if field != "time"
                for value in hourly[field]
            ):
                raise ValueError("Empty hourly response")
        elif "features" in payload and not payload["features"]:
            raise ValueError("Empty ECCC response")
        return {"payload": payload, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "cached": False, "source": url, "error": None}
    except (requests.RequestException, ValueError, KeyError) as exc:
        path = SAMPLE / f"{key}.json"
        if not path.exists():
            return {"payload": {}, "retrieved_at": None, "cached": True,
                    "source": url, "error": f"No snapshot available: {exc}"}
        envelope = json.loads(path.read_text(encoding="utf-8"))
        return {**envelope, "cached": True, "error": str(exc)}


def coordinates(city: str) -> dict:
    """Coordinates and UTC epoch timestamps for DST-safe local aggregation."""
    lat, lon = LOCATIONS[city]
    return {"latitude": lat, "longitude": lon, "timeformat": "unixtime",
            "timezone": "UTC"}


@st.cache_data(ttl=LIVE_TTL, show_spinner=False)
def weather_forecast(city: str, offline: bool = False) -> dict:
    """Retrieve seven days of hourly weather plus recent gap-fill days."""
    return fetch(FORECAST_URL, {**coordinates(city), "hourly": ",".join(WEATHER),
                 "wind_speed_unit": "kmh", "past_days": 7, "forecast_days": 8},
                 f"{city}_forecast", offline)


@st.cache_data(ttl=HISTORICAL_TTL, show_spinner=False)
def weather_history(city: str, today: date, offline: bool = False) -> dict:
    """Retrieve reanalysis up to its publication delay; forecast fills recent gap."""
    return fetch(ARCHIVE_URL, {**coordinates(city), "hourly": ",".join(WEATHER),
                 "wind_speed_unit": "kmh", "start_date": str(today - timedelta(days=91)),
                 "end_date": str(today - timedelta(days=5))}, f"{city}_history", offline)


@st.cache_data(ttl=LIVE_TTL, show_spinner=False)
def ozone(city: str, offline: bool = False) -> dict:
    """CAMS modelled ozone, up to ninety past days; not station observations."""
    return fetch(OZONE_URL, {**coordinates(city), "hourly": "ozone", "past_days": 92,
                 "forecast_days": 5}, f"{city}_ozone", offline)


@st.cache_data(ttl=LIVE_TTL, show_spinner=False)
def aqhi(kind: str = "observations", offline: bool = False, city: str = "Toronto") -> dict:
    """Fetch the selected official AQHI area; never substitute another city."""
    if kind not in {"observations", "forecasts"}:
        raise ValueError("AQHI kind must be observations or forecasts")
    collection = f"aqhi-{kind}-realtime"
    station = LOCATION_DETAILS[city]["aqhi_id"]
    if station is None:
        return {"payload": {"features": []}, "retrieved_at": None, "cached": False,
                "source": f"{ECCC_URL}/aqhi-stations/items",
                "error": "No official AQHI area configured for this location."}
    params = {"f": "json", "location_id": station, "limit": 1000}
    if kind == "observations":
        params["latest"] = "true"
    envelope = fetch(f"{ECCC_URL}/{collection}/items", params, f"aqhi_{city}_{kind}", offline)
    # Constrain fallback as well as live responses to the requested station.
    features = envelope["payload"].get("features", [])
    envelope["payload"]["features"] = [f for f in features if f["properties"].get("location_id") == station]
    return envelope


@st.cache_data(ttl=HISTORICAL_TTL, show_spinner=False)
def baseline(offline: bool = False) -> pd.DataFrame:
    """Load the canonical R airquality dataset, falling back to its saved CSV."""
    from statsmodels.datasets import get_rdataset
    if not offline and os.getenv("AIR_QUALITY_OFFLINE") != "1":
        for _ in range(2):
            try:
                frame = get_rdataset("airquality", "datasets", cache=False).data
                frame.attrs["cached"] = False
                frame.attrs["retrieved_at"] = datetime.now(timezone.utc).isoformat()
                return frame
            except (OSError, ValueError, TimeoutError):
                pass
    frame = pd.read_csv(SAMPLE / "airquality.csv")
    frame.attrs["cached"] = True
    provenance = SAMPLE / "provenance.json"
    frame.attrs["retrieved_at"] = json.loads(provenance.read_text())["baseline_retrieved_at"] if provenance.exists() else "unknown"
    return frame
