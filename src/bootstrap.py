"""Route legacy pages-directory deep links through shared app initialization."""
import streamlit as st


def require_context(page: str) -> None:
    """Initialize a fresh direct-link session, then return to its requested page."""
    if "ctx" not in st.session_state:
        st.session_state["_bootstrap_page"] = page
        st.switch_page("streamlit_app.py")
