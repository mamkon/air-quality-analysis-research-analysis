"""Execute every page against real saved data without internet."""
import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.bootstrap import require_context
from src.context import load


@pytest.mark.parametrize("page", ["overview", "method", "live", "framework", "simulator", "audience", "limitations"])
def test_page_offline(page: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run actual page scripts, including figures and widgets."""
    monkeypatch.setenv("AIR_QUALITY_OFFLINE", "1")
    context = load("Toronto", True)
    path = Path(__file__).resolve().parents[1] / "app" / "pages" / f"{page}.py"
    test = AppTest.from_file(str(path), default_timeout=60)
    test.session_state.ctx = context
    test.run()
    assert not test.exception, str(test.exception)


def test_entry_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Entry point renders fallback banners and navigation in a full outage."""
    monkeypatch.setenv("AIR_QUALITY_OFFLINE", "1")
    path = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
    test = AppTest.from_file(str(path), default_timeout=60).run()
    assert not test.exception, str(test.exception)
    assert any("Showing cached data" in warning.value for warning in test.warning)
    assert os.getenv("AIR_QUALITY_OFFLINE") == "1"


def test_direct_link_bootstrap(monkeypatch: pytest.MonkeyPatch) -> None:
    """A fresh page remembers its destination and switches through the entry point."""
    from src import bootstrap
    state = {}
    switches = []
    monkeypatch.setattr(bootstrap.st, "session_state", state)
    monkeypatch.setattr(bootstrap.st, "switch_page", switches.append)
    require_context("method.py")
    assert state["_bootstrap_page"] == "method.py"
    assert switches == ["streamlit_app.py"]
    state["ctx"] = {"ready": True}
    require_context("method.py")
    assert len(switches) == 1


@pytest.mark.parametrize("city", ["Ottawa", "Kenora", "Fort Severn"])
def test_ontario_overview(city: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Overview renders local AQHI availability and regional time zones."""
    monkeypatch.setenv("AIR_QUALITY_OFFLINE", "1")
    path = Path(__file__).resolve().parents[1] / "app" / "pages" / "overview.py"
    test = AppTest.from_file(str(path), default_timeout=60)
    test.session_state.ctx = load(city, True)
    test.run()
    assert not test.exception, str(test.exception)
    assert any(city in line.value for line in test.markdown)


def test_region_selector(monkeypatch: pytest.MonkeyPatch) -> None:
    """Selecting an Ontario region and Ottawa reloads the correct location model."""
    monkeypatch.setenv("AIR_QUALITY_OFFLINE", "1")
    path = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
    test = AppTest.from_file(str(path), default_timeout=60)
    # Seed the public widget state; interactive navigation is also browser-tested.
    test.session_state["region"] = "Eastern Ontario"
    test.session_state["city"] = "Ottawa"
    test.run()
    assert not test.exception, str(test.exception)
    assert test.session_state.ctx["city"] == "Ottawa"
    assert "Toronto" not in test.sidebar.selectbox[1].options
