"""Explicit temporal alignment, coverage gates and unit conversions."""
import pandas as pd

from src.config import TIMEZONE


def ugm3_to_ppb(value: float) -> float:
    """Convert ozone using 1.96 µg/m³ per ppb at 25°C and 1 atm."""
    return value / 1.96


def hourly(envelope: dict, timezone: str = TIMEZONE) -> pd.DataFrame:
    """Decode UTC epoch timestamps into DST-aware local timestamps."""
    frame = pd.DataFrame(envelope.get("payload", {}).get("hourly", {}))
    if frame.empty:
        return frame
    frame["time"] = pd.to_datetime(frame["time"], unit="s", utc=True).dt.tz_convert(timezone)
    return frame.set_index("time")


def daily_weather(frame: pd.DataFrame) -> pd.DataFrame:
    """Require complete local days; integrate hourly mean W/m² into MJ/m²."""
    if frame.empty:
        return pd.DataFrame(columns=["temp", "wind", "solar"])
    groups = frame.resample("D")
    daily = groups.agg({"temperature_2m": "max", "wind_speed_10m": "mean",
                        "shortwave_radiation": "sum"})
    # Local days contain 23/24/25 hours across DST changes.
    expected = pd.Series([((d + pd.DateOffset(days=1)).tz_convert("UTC") -
                           d.tz_convert("UTC")).total_seconds() / 3600
                          for d in daily.index], index=daily.index)
    valid = groups.count().ge(expected, axis=0).all(axis=1)
    daily["shortwave_radiation"] *= 0.0036
    daily = daily.rename(columns={"temperature_2m": "temp", "wind_speed_10m": "wind",
                                  "shortwave_radiation": "solar"})
    return daily.loc[valid]


def daily_ozone(frame: pd.DataFrame) -> pd.DataFrame:
    """Mean ozone for local hours 13, 14 and 15; require all three readings."""
    if frame.empty:
        return pd.DataFrame(columns=["ozone"])
    afternoon = frame.loc[frame.index.hour.isin([13, 14, 15]), "ozone"]
    groups = afternoon.resample("D")
    result = (groups.mean() / 1.96).where(groups.count() == 3).dropna()
    return result.to_frame("ozone")


def combine_weather(history: pd.DataFrame, forecast: pd.DataFrame) -> pd.DataFrame:
    """Prefer archive weather where available; fill the recent gap with forecast."""
    frame = pd.concat([history, forecast])
    return frame.loc[~frame.index.duplicated(keep="first")].sort_index()
