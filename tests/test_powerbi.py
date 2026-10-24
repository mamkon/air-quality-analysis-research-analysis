"""Validate native report integrity and scenario arithmetic against Python OLS."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.modeling import fit, predict

PBI = Path(__file__).resolve().parents[1] / "powerbi"


def test_native_project_structure() -> None:
    """All seven native pages and their semantic model references are present."""
    shortcut = next(PBI.glob("*.pbip"))
    report = PBI / json.loads(shortcut.read_text())["artifacts"][0]["report"]["path"]
    reference = json.loads((report / "definition.pbir").read_text())["datasetReference"]["byPath"]["path"]
    model = json.loads((report / reference / "model.bim").read_text())
    assert len(model["model"]["tables"]) == 23
    assert len(model["model"]["relationships"]) == 6
    measures = next(t["measures"] for t in model["model"]["tables"] if t["name"] == "LocationSummary")
    assert len(measures) == 40
    metadata = json.loads((report / "definition" / "pages" / "pages.json").read_text())
    assert len(metadata["pageOrder"]) == 7
    for page in metadata["pageOrder"]:
        assert (report / "definition" / "pages" / page / "page.json").exists()
        assert list((report / "definition" / "pages" / page / "visuals").glob("*/visual.json"))


@pytest.mark.parametrize("city", ["Toronto", "Ottawa", "Kenora"])
def test_powerbi_scenario_interval_matches_ols(city: str) -> None:
    """The exported DAX inputs reproduce the exact fitted OLS prediction limits."""
    params = pd.read_csv(PBI / "data" / "ModelParameters.csv").set_index("Location").loc[city]
    history = pd.read_csv(PBI / "data" / "History.csv")
    source = history.loc[history.Location == city].rename(columns={
        "ActualOzone": "ozone", "Temperature": "temp", "Wind": "wind", "SolarEnergy": "solar"})
    model = fit(source)
    x = np.array([1.0, 26.0, 13.0, 230.0 * 0.0864])
    estimate = params.Intercept + params.TempCoef * x[1] + params.WindCoef * x[2] + params.SolarCoef * x[3]
    inverse = np.zeros((4, 4))
    for i in range(4):
        for j in range(i, 4):
            inverse[i, j] = inverse[j, i] = params[f"Inv{i}{j}"]
    half = params.TCritical * params.ResidualSigma * np.sqrt(1 + x @ inverse @ x)
    actual = predict(model, pd.DataFrame({"temp": [x[1]], "wind": [x[2]], "solar": [x[3]]})).iloc[0]
    assert estimate == pytest.approx(actual.predicted, abs=1e-8)
    assert estimate - half == pytest.approx(actual.lower, abs=1e-8)
    assert estimate + half == pytest.approx(actual.upper, abs=1e-8)


def test_powerbi_exports_keep_unknown_aqhi() -> None:
    """The native report does not turn unavailable official readings into zero."""
    summary = pd.read_csv(PBI / "data" / "LocationSummary.csv").set_index("Location")
    assert len(summary) == 47
    assert pd.isna(summary.loc["Kenora", "AQHI"])
    assert pd.notna(summary.loc["Ottawa", "AQHI"])


def test_native_slicers_select_without_hiding_other_locations() -> None:
    """Default Toronto must cross-filter the page while retaining other choices."""
    report = next(PBI.glob("*.Report"))
    assert json.loads((report / "definition/version.json").read_text())["version"] == "2.0.0"
    for path in report.glob("definition/pages/*/visuals/LocationSelector/visual.json"):
        visual = json.loads(path.read_text())
        assert "filterConfig" not in visual
        selection = visual["visual"]["objects"]["general"][0]["properties"]["filter"]["filter"]
        assert selection["From"][0]["Entity"] == "Locations"
        assert selection["Where"][0]["Condition"]["In"]["Values"] == [[{"Literal": {"Value": "'Toronto'"}}]]
