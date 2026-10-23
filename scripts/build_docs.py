"""Regenerate recruiter findings and daily CSVs from source snapshots."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from src.api_clients import baseline  # noqa: E402
from src.config import LOCATION_DETAILS, LOCATIONS, REGIONS, ROOT, SAMPLE  # noqa: E402
from src.context import load  # noqa: E402
from src.decisions import confusion  # noqa: E402
from src.modeling import baseline_frame, baseline_sensitivity, fit, metrics  # noqa: E402


def main() -> None:
    """Write evidence and documentation without hard-coded model findings."""
    raw = baseline_frame(baseline(True))
    base = raw.dropna()
    baseline_metrics = metrics(fit(base))
    sensitivity = baseline_sensitivity(raw)
    sensitivity.to_csv(ROOT / "docs" / "baseline_sensitivity.csv", index=False)
    records = []
    for city in LOCATIONS:
        context = load(city, True)
        context["past"].to_csv(SAMPLE / f"daily_{city}.csv")
        evaluation = context["evaluation"]
        records.append({"city": city, **metrics(context["model"]),
                        "heldout_n": len(evaluation),
                        "heldout_rmse_ppb": float(evaluation.residual.pow(2).mean() ** 0.5),
                        "event_support_60": confusion(evaluation.ozone, evaluation.predicted, 60)["TP"] +
                                            confusion(evaluation.ozone, evaluation.predicted, 60)["FN"]})
    results = {"generated_at": datetime.now(timezone.utc).isoformat(),
               "baseline": baseline_metrics, "baseline_sensitivity": sensitivity.to_dict("records"),
               "cities": records}
    (ROOT / "docs" / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    pd.DataFrame(records).to_csv(ROOT / "docs" / "results.csv", index=False)
    toronto = records[0]
    template = (ROOT / "docs" / "README.template.md").read_text(encoding="utf-8")
    values = {"BASE_N": str(baseline_metrics["n"]), "BASE_R2": f"{baseline_metrics['Adjusted R²']:.3f}",
              "GTA_R2": f"{toronto['Adjusted R²']:.3f}", "GTA_RMSE": f"{toronto['heldout_rmse_ppb']:.2f}",
              "GTA_N": str(toronto["n"]), "EVENTS": str(toronto["event_support_60"])}
    mean = sensitivity.loc[sensitivity.Method == "Mean"].iloc[0]
    values.update({"MEAN_N": str(int(mean["n"])), "MEAN_R2": f"{mean['R²']:.3f}"})
    values.update({"LOCATION_COUNT": str(len(LOCATIONS)), "REGION_COUNT": str(len(REGIONS)),
                   "AQHI_COUNT": str(sum(bool(point["aqhi_id"]) for point in LOCATION_DETAILS.values()))})
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    (ROOT / "README.md").write_text(template, encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
