"""Build reviewed Ontario selectors from official ECCC and geocoding metadata."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.api_clients import request_json  # noqa: E402


def main() -> None:
    """Save station identity, point coordinates, local timezone and regional grouping."""
    url = "https://api.weather.gc.ca/collections/aqhi-stations/items"
    stations = request_json(url, {"f": "json", "limit": 1000})
    assert stations["numberMatched"] <= 1000
    regions = {
        "Greater Toronto & Hamilton": ["Toronto", "Toronto Downtown", "Toronto East", "Toronto North", "Toronto West", "Hamilton", "Hamilton Downtown", "Hamilton Mountain", "Hamilton West", "Mississauga", "Brampton", "Oakville", "Burlington", "Milton", "Newmarket", "Oshawa"],
        "Southwestern Ontario": ["Windsor", "Windsor Downtown", "Windsor West", "London", "Sarnia", "Chatham", "Port Stanley", "Grand Bend", "Tiverton"],
        "Central & Southern Ontario": ["Barrie", "Brantford", "Guelph", "Kitchener", "St. Catharines", "Dorset", "Parry Sound"],
        "Eastern Ontario": ["Ottawa", "Kingston", "Belleville", "Cornwall", "Peterborough"],
        "Northeastern Ontario": ["North Bay", "Sudbury", "Sault Ste. Marie", "Timmins", "Moosonee"],
        "Northwestern & Far Northern Ontario": ["Thunder Bay", "Kenora", "Dryden", "Sioux Lookout", "Fort Severn"],
    }
    original = {"Toronto": (43.6532, -79.3832), "Mississauga": (43.5890, -79.6441),
                "Oakville": (43.4675, -79.6877), "Hamilton": (43.2557, -79.8711), "Brampton": (43.7315, -79.7624)}
    locations = {}
    for feature in stations["features"]:
        props = feature["properties"]
        if props.get("eccc_administrative-zone") != "ont":
            continue
        city = props["location_name_en"]
        lon, lat = feature["geometry"]["coordinates"]
        lat, lon = original.get(city, (lat, lon))
        locations[city] = {"latitude": lat, "longitude": lon, "timezone": "America/Toronto",
                           "aqhi_id": props["location_id"], "aqhi_name": city}
    for city in ["Kenora", "Dryden", "Sioux Lookout", "Timmins", "Moosonee", "Fort Severn"]:
        response = request_json("https://geocoding-api.open-meteo.com/v1/search", {
            "name": city, "count": 10, "countryCode": "CA", "format": "json"})
        point = next(p for p in response["results"] if p.get("admin1") == "Ontario")
        locations[city] = {"latitude": point["latitude"], "longitude": point["longitude"],
                           "timezone": point["timezone"], "aqhi_id": None, "aqhi_name": None}
    for city, point in locations.items():
        point["region"] = next(name for name, members in regions.items() if city in members)
    ordered = {city: locations[city] for city in ["Toronto", *sorted(set(locations) - {"Toronto"})]}
    data = {"retrieved_at": datetime.now(timezone.utc).isoformat(), "station_source": url,
            "geocoding_source": "https://geocoding-api.open-meteo.com/v1/search", "locations": ordered}
    (ROOT / "data" / "ontario_locations.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Saved {len(ordered)} Ontario locations; {sum(bool(p['aqhi_id']) for p in ordered.values())} official AQHI areas.")


if __name__ == "__main__":
    main()
