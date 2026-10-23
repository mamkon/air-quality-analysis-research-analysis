"""Central, reviewable settings; all weather inputs use SI units."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample"
LOCATION_DETAILS = json.loads((ROOT / "data" / "ontario_locations.json").read_text())["locations"]
LOCATIONS = {city: (point["latitude"], point["longitude"]) for city, point in LOCATION_DETAILS.items()}
REGIONS = list(dict.fromkeys(point["region"] for point in LOCATION_DETAILS.values()))
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OZONE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
ECCC_URL = "https://api.weather.gc.ca/collections"
TIMEZONE = "America/Toronto"
LIVE_TTL = 3600
HISTORICAL_TTL = 86400
TIMEOUT = 20
WEATHER = ["temperature_2m", "wind_speed_10m", "shortwave_radiation"]
FEATURES = ["temp", "wind", "solar"]
TIERS = [(50, "Good", "#0072B2"), (60, "Moderate", "#E69F00"),
         (70, "High", "#D55E00"), (float("inf"), "Very High", "#CC79A7")]
AUTHOR = "Mercy Mamkon Oyeleke"
