"""Explicit opt-in live integration verification, separate from offline CI."""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streamlit.testing.v1 import AppTest  # noqa: E402

from src.config import LOCATION_DETAILS, LOCATIONS, ROOT  # noqa: E402
from src.context import load  # noqa: E402


def main() -> None:
    """Check all live sources/cities and execute every page with live context."""
    records = []
    toronto = None
    with ThreadPoolExecutor(max_workers=3) as executor:
        contexts = list(executor.map(load, LOCATIONS))
    for city, context in zip(LOCATIONS, contexts):
        assert all(not s["cached"] for s in context["sources"].values()), city
        records.append({"city": city, "days": len(context["past"]),
                        "official_aqhi_area": LOCATION_DETAILS[city]["aqhi_id"],
                        "adjusted_r2": context["model"].rsquared_adj,
                        "heldout_rmse": float(context["evaluation"].residual.pow(2).mean()**0.5),
                        "sources": {k: v["retrieved_at"] for k, v in context["sources"].items()}})
        if city == "Toronto":
            toronto = context
    for path in sorted((ROOT / "app" / "pages").glob("*.py")):
        test = AppTest.from_file(str(path), default_timeout=90)
        test.session_state.ctx = toronto
        test.run()
        assert not test.exception, f"{path}: {test.exception}"
    test = AppTest.from_file(str(ROOT / "app" / "streamlit_app.py"), default_timeout=90).run()
    assert not test.exception, str(test.exception)
    (ROOT / "docs" / "live_verification.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"All {len(LOCATIONS)} Ontario locations fetched live weather/ozone and available AQHI; all seven pages and entry point passed.")


if __name__ == "__main__":
    main()
