"""UI utilities and shared components for the Infrahub Service Catalog."""

from typing import Optional

import streamlit as st


def display_logo() -> None:
    """Display the Infrahub branding in the sidebar."""
    st.sidebar.markdown("### Infrahub Service Catalog")


def display_error(message: str, details: Optional[str] = None) -> None:
    """Display an error message with optional details."""
    st.error(message)
    if details:
        with st.expander("Error Details"):
            st.code(details, language=None)


def display_success(message: str) -> None:
    """Display a success message."""
    st.success(message)


def display_progress(message: str, progress: float) -> None:
    """Display a progress bar with a message."""
    st.text(message)
    st.progress(progress)
