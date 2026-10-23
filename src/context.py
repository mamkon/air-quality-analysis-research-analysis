"""Assemble page context and report all source ages without silently mixing dates."""
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from src import api_clients as api
from src.config import LOCATION_DETAILS
from src.modeling import validate
from src.transform import combine_weather, daily_ozone, daily_weather, hourly


def load(city: str, offline: bool = False) -> dict:
    """Collect sources, past-only training data and independent forecast weather."""
    timezone = LOCATION_DETAILS[city]["timezone"]
    now = pd.Timestamp(datetime.now(ZoneInfo(timezone)))
    sources = {"Weather archive": api.weather_history(city, now.date(), offline),
               "Weather forecast": api.weather_forecast(city, offline),
               "CAMS ozone": api.ozone(city, offline),
               "Local AQHI observations": api.aqhi("observations", offline, city),
               "Local AQHI forecasts": api.aqhi("forecasts", offline, city)}
    history = hourly(sources["Weather archive"], timezone)
    forecast = hourly(sources["Weather forecast"], timezone)
    combined = combine_weather(history, forecast)
    ozone_hourly = hourly(sources["CAMS ozone"], timezone)
    daily = daily_weather(combined).join(daily_ozone(ozone_hourly), how="inner").dropna()
    past = daily.loc[daily.index < now.normalize()].tail(90)
    model, evaluation, training_model = validate(past)
    future = daily_weather(forecast)
    future = future.loc[future.index >= now.normalize()].head(7)
    return dict(city=city, now=now, timezone=timezone, sources=sources, past=past, model=model,
                evaluation=evaluation, training_model=training_model, future=future,
                ozone_hourly=ozone_hourly, offline=offline)


def aqhi_table(envelope: dict) -> pd.DataFrame:
    """Preserve official property names for transparent observation/forecast context."""
    table = pd.DataFrame([f["properties"] for f in envelope["payload"].get("features", [])])
    if len(table) and "publication_datetime" in table:
        table = table.loc[table.publication_datetime == table.publication_datetime.max()]
    if len(table) and "forecast_datetime" in table:
        table = table.sort_values("forecast_datetime")
    return table
