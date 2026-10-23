"""Scientific correctness, failure handling and page execution tests."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import requests

from src import api_clients as api
from src.config import LOCATION_DETAILS, LOCATIONS, SAMPLE
from src.context import aqhi_table, load
from src.decisions import confusion, risk
from src.modeling import baseline_frame, baseline_sensitivity, fit, predict, validate
from src.transform import daily_ozone, daily_weather, hourly, ugm3_to_ppb


@pytest.mark.parametrize("value,expected", [(0, 0), (196, 100), (39.2, 20)])
def test_conversion(value: float, expected: float) -> None:
    """Reference ozone conversions preserve the specified assumption."""
    assert ugm3_to_ppb(value) == pytest.approx(expected)


@pytest.mark.parametrize("value,expected", [(0, "Good"), (49.99, "Good"), (50, "Moderate"),
    (60, "High"), (70, "Very High"), (-1, "Unavailable"), (np.nan, "Unavailable")])
def test_risk(value: float, expected: str) -> None:
    """Boundary behaviour is deliberate and negative predictions are not healthy."""
    assert risk(value) == expected


def test_aggregation() -> None:
    """Known full-day energy and afternoon-only target; missing hours rejected."""
    index = pd.date_range("2026-07-01", periods=24, freq="h", tz="America/Toronto")
    weather = pd.DataFrame({"temperature_2m": np.arange(24), "wind_speed_10m": 10,
                            "shortwave_radiation": 100}, index=index)
    day = daily_weather(weather).iloc[0]
    assert day.temp == 23
    assert day.wind == 10
    assert day.solar == pytest.approx(8.64)
    assert daily_weather(weather.iloc[:-1]).empty
    ozone = pd.DataFrame({"ozone": 196.0}, index=index)
    ozone.loc[ozone.index.hour < 13, "ozone"] = 0
    assert daily_ozone(ozone).ozone.iloc[0] == pytest.approx(100)
    assert daily_ozone(ozone.drop(index[14])).empty


@pytest.mark.parametrize("start,periods", [("2026-03-08", 23), ("2026-11-01", 25)])
def test_dst_coverage(start: str, periods: int) -> None:
    """Full spring and autumn local days remain valid."""
    index = pd.date_range(start, periods=periods, freq="h", tz="America/Toronto")
    weather = pd.DataFrame({"temperature_2m": 20, "wind_speed_10m": 10,
                            "shortwave_radiation": 100}, index=index)
    assert len(daily_weather(weather)) == 1


@pytest.mark.parametrize("key", ["Toronto_forecast", "Toronto_history", "Toronto_ozone",
                                 "aqhi_observations", "aqhi_forecasts"])
def test_mocked_api_and_fallback(monkeypatch: pytest.MonkeyPatch, key: str) -> None:
    """Every external API uses a saved JSON fixture and falls back on failure."""
    fixture = Path(__file__).parent / "fixtures" / f"{key}.json"
    envelope = json.loads(fixture.read_text())
    monkeypatch.setattr(api, "request_json", lambda *args: envelope["payload"])
    live = api.fetch("https://example.invalid", {}, key)
    assert not live["cached"]
    def fail(*args) -> dict:
        """Simulate total provider outage."""
        raise requests.ConnectionError("down")
    monkeypatch.setattr(api, "request_json", fail)
    fallback = api.fetch("https://example.invalid", {}, key)
    assert fallback["cached"]
    assert fallback["payload"] == envelope["payload"]
    assert fallback["retrieved_at"] == envelope["retrieved_at"]


def test_request_timeout_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Transport passes a timeout, mounts retries and checks HTTP status."""
    seen = {}
    class Response:
        """Minimal successful response."""
        def raise_for_status(self) -> None:
            """Record status check."""
            seen["status"] = True
        def json(self) -> dict:
            """Return parsed JSON."""
            return {"ok": True}
    def get(self, url: str, **kwargs) -> Response:
        """Inspect bounded transport options."""
        seen.update(kwargs)
        assert self.adapters["https://"].max_retries.total == 2
        return Response()
    monkeypatch.setattr(requests.Session, "get", get)
    assert api.request_json("https://example.invalid", {}) == {"ok": True}
    assert seen["timeout"] > 0 and seen["status"]


def test_baseline_model() -> None:
    """Canonical sample has the expected complete-case size and reasonable fit."""
    frame = baseline_frame(pd.read_csv(SAMPLE / "airquality.csv")).dropna()
    model = fit(frame)
    assert model.nobs == 111
    assert 0.55 < model.rsquared < 0.7
    result = predict(model, frame.head())
    assert (result.lower < result.predicted).all()
    assert (result.upper > result.predicted).all()


def test_baseline_sensitivity_reconciles_reference() -> None:
    """Reproduce supplied rounded mean-imputation results without altering raw data."""
    frame = baseline_frame(pd.read_csv(SAMPLE / "airquality.csv"))
    original = frame.copy(deep=True)
    table = baseline_sensitivity(frame).set_index("Method")
    mean = table.loc["Mean"]
    assert mean["n"] == 153
    assert mean["Imputed ozone targets"] == 37
    assert mean["R²"] == pytest.approx(0.480025495, abs=1e-8)
    assert mean["Intercept"] == pytest.approx(-38.2232, abs=0.0001)
    assert mean["Temperature coefficient (ppb/°F)"] == pytest.approx(1.2413, abs=0.0001)
    assert mean["Wind coefficient (ppb/mph)"] == pytest.approx(-2.7173, abs=0.0001)
    assert mean["Solar coefficient (ppb/Langley)"] == pytest.approx(0.0577, abs=0.0001)
    assert table.loc["Complete case", "n"] == 111
    assert table.loc["Complete case", "Imputed ozone targets"] == 0
    assert table.loc["Median", "n"] == 153
    pd.testing.assert_frame_equal(frame, original)


def test_validation() -> None:
    """Chronological holdout never includes validation targets in fit."""
    history = hourly(json.loads((SAMPLE / "Toronto_history.json").read_text()))
    ozone = hourly(json.loads((SAMPLE / "Toronto_ozone.json").read_text()))
    frame = daily_weather(history).join(daily_ozone(ozone)).dropna()
    final, evaluation, training = validate(frame)
    assert training.nobs < final.nobs
    assert max(training.model.data.row_labels) < evaluation.index.min()
    assert evaluation.residual.notna().all()


def test_confusion() -> None:
    """All four cases and no-event support are handled explicitly."""
    result = confusion(pd.Series([70, 70, 20, 20]), pd.Series([70, 20, 70, 20]), 60)
    assert all(result[k] == 1 for k in ["TP", "TN", "FP", "FN"])
    assert result["Recall"] == result["Precision"] == 0.5
    assert np.isnan(confusion(pd.Series([20]), pd.Series([20]), 60)["Recall"])


def test_baseline_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Canonical data retrieval retries and surfaces its fallback provenance."""
    import statsmodels.datasets
    attempts = []
    def fail(*args, **kwargs) -> None:
        """Simulate baseline source outage."""
        attempts.append(1)
        raise OSError("source down")
    monkeypatch.setattr(statsmodels.datasets, "get_rdataset", fail)
    api.baseline.clear()
    frame = api.baseline()
    assert len(attempts) == 2
    assert frame.attrs["cached"]
    assert frame.attrs["retrieved_at"] != "unknown"
    assert len(frame) == 153


def test_empty_payload_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful HTTP with unusable data is still a data failure."""
    monkeypatch.setattr(api, "request_json", lambda *args: {"hourly": {"time": [], "ozone": []}})
    assert api.fetch("https://example.invalid", {}, "Toronto_ozone")["cached"]


@pytest.mark.parametrize("city", list(LOCATIONS))
def test_ontario_location_offline(city: str) -> None:
    """Every selectable location has real complete training and forecast snapshots."""
    context = load(city, True)
    assert len(context["past"]) >= 60
    assert context["timezone"] == LOCATION_DETAILS[city]["timezone"]
    assert str(context["past"].index.tz) == context["timezone"]
    saved_forecast = daily_weather(hourly(context["sources"]["Weather forecast"], context["timezone"]))
    assert len(saved_forecast) >= 7
    # Snapshots preserve their dates; an expired forecast legitimately has no
    # current days. CI must remain deterministic after the capture date.
    assert context["future"].index.min() >= context["now"].normalize() if len(context["future"]) else True
    for label in ["Weather archive", "Weather forecast", "CAMS ozone"]:
        assert context["sources"][label]["retrieved_at"] is not None
    table = aqhi_table(context["sources"]["Local AQHI observations"])
    station = LOCATION_DETAILS[city]["aqhi_id"]
    if station:
        assert len(table)
        assert set(table.location_id) == {station}
    else:
        assert table.empty


@pytest.mark.parametrize("city", ["Ottawa", "Windsor", "Thunder Bay"])
def test_aqhi_uses_selected_area(monkeypatch: pytest.MonkeyPatch, city: str) -> None:
    """Queries and returned values cannot silently substitute Toronto's AQHI."""
    station = LOCATION_DETAILS[city]["aqhi_id"]
    payload = json.loads((SAMPLE / f"aqhi_{city}_observations.json").read_text())["payload"]
    def respond(url: str, params: dict) -> dict:
        """Inspect exact official identity and latest-observation filtering."""
        assert params["location_id"] == station
        assert params["latest"] == "true"
        assert "bbox" not in params
        return payload
    monkeypatch.setattr(api, "request_json", respond)
    api.aqhi.clear()
    result = api.aqhi(city=city)
    assert not result["cached"]
    assert set(aqhi_table(result).location_id) == {station}


def test_missing_aqhi_never_substitutes_city(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unmonitored northern points have explicit missing official AQHI context."""
    def unexpected(*args, **kwargs) -> dict:
        """A missing official area must not trigger a proxy request."""
        raise AssertionError("Unexpected AQHI request")
    monkeypatch.setattr(api, "request_json", unexpected)
    api.aqhi.clear()
    result = api.aqhi(city="Kenora")
    assert not result["payload"]["features"]
    assert "No official AQHI" in result["error"]


def test_western_ontario_local_hours() -> None:
    """UTC epochs become the correct Central-time afternoon, not Toronto time."""
    envelope = {"payload": {"hourly": {"time": [1782928800], "ozone": [196]}}}
    western = hourly(envelope, "America/Winnipeg")
    eastern = hourly(envelope, "America/Toronto")
    assert eastern.index[0].hour == western.index[0].hour + 1


def test_aqhi_forecasts_latest_publication() -> None:
    """Old forecasts cannot overwrite values from the latest issue."""
    envelope = json.loads((SAMPLE / "aqhi_Ottawa_forecasts.json").read_text())
    table = aqhi_table(envelope)
    all_issues = [f["properties"]["publication_datetime"] for f in envelope["payload"]["features"]]
    assert set(table.publication_datetime) == {max(all_issues)}
