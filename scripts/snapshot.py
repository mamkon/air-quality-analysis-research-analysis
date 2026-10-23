"""Explicitly refresh distributable source snapshots; never fabricate fallback data."""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import api_clients as api  # noqa: E402
from src.config import LOCATION_DETAILS, LOCATIONS, SAMPLE  # noqa: E402


def save_city(city: str) -> None:
    """Fetch genuine per-location snapshots, keeping existing weather unless refreshed."""
    today = datetime.now(ZoneInfo(LOCATION_DETAILS[city]["timezone"])).date()
    for key, call in [("forecast", lambda: api.weather_forecast(city)),
                      ("history", lambda: api.weather_history(city, today)),
                      ("ozone", lambda: api.ozone(city))]:
        path = SAMPLE / f"{city}_{key}.json"
        if path.exists() and "--refresh-all" not in sys.argv:
            continue
        envelope = call()
        if not envelope["cached"]:
            path.write_text(json.dumps(envelope), encoding="utf-8")
        else:
            print(city, key, envelope.get("error"), flush=True)
    for kind in ["observations", "forecasts"]:
        if (SAMPLE / f"aqhi_{city}_{kind}.json").exists() and "--refresh-all" not in sys.argv:
            continue
        envelope = api.aqhi(kind, city=city)
        if not envelope["cached"] and envelope["payload"].get("features"):
            (SAMPLE / f"aqhi_{city}_{kind}.json").write_text(json.dumps(envelope), encoding="utf-8")
        elif envelope["cached"]:
            print(city, kind, envelope.get("error"), flush=True)
    print(f"Saved sources: {city}", flush=True)


def main() -> None:
    """Save successful API envelopes with original timestamps and baseline CSV."""
    SAMPLE.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(save_city, LOCATIONS))
    baseline = api.baseline()
    if not baseline.attrs.get("cached"):
        baseline.to_csv(SAMPLE / "airquality.csv", index=False)
        (SAMPLE / "provenance.json").write_text(json.dumps({
            "baseline_retrieved_at": datetime.now(timezone.utc).isoformat(),
            "source": "statsmodels.datasets.get_rdataset('airquality', 'datasets')"}), encoding="utf-8")


if __name__ == "__main__":
    main()
