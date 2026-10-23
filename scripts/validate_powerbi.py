"""Validate native Power BI JSON against Microsoft's public schemas."""
import json
from pathlib import Path

import jsonschema
import requests

ROOT = Path(__file__).resolve().parents[1]
CACHE: dict[str, dict] = {}


def retrieve(uri: str) -> dict:
    """Retrieve each official schema only once during this verification run."""
    if uri not in CACHE:
        if not uri.startswith("https://developer.microsoft.com/json-schemas/"):
            raise ValueError(f"Unexpected schema host: {uri}")
        response = requests.get(uri, timeout=30)
        response.raise_for_status()
        CACHE[uri] = response.json()
        if "$id" in CACHE[uri]:
            CACHE[CACHE[uri]["$id"]] = CACHE[uri]
    return CACHE[uri]


def main() -> None:
    """Check every declared schema; Power BI Desktop separately validates DAX/M."""
    count = 0
    failures = []
    paths = list((ROOT / "powerbi").rglob("*.json")) + list((ROOT / "powerbi").rglob("*.pbip")) + list((ROOT / "powerbi").rglob("*.pbir")) + list((ROOT / "powerbi").rglob("*.pbism"))
    for path in paths:
        if ".pbi" in path.parts:
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if "$schema" not in value:
            continue
        uri = value["$schema"]
        schema = retrieve(uri)
        resolver = jsonschema.RefResolver(uri, schema, handlers={"https": retrieve})
        errors = list(jsonschema.Draft7Validator(schema, resolver=resolver).iter_errors(value))
        if errors:
            failures.extend(f"{path.relative_to(ROOT)}: {list(error.path)} {error.message}" for error in errors)
        count += 1
    if failures:
        raise ValueError("\n".join(failures))
    print(f"Validated {count} native Power BI files against {len(CACHE)} official schema resources.")


if __name__ == "__main__":
    main()
