"""Infrahub client for the visitor using the current browser session."""

import streamlit as st  # type: ignore[import-untyped]

from .api import InfrahubAPIError, InfrahubClient
from .config import INFRAHUB_ADDRESS, INFRAHUB_API_TOKEN, INFRAHUB_UI_URL

_CLIENT_KEY = "infrahub_client"


def get_client() -> InfrahubClient:
    """Return the Infrahub client for this browser session.

    When INFRAHUB_API_TOKEN is set, as in the local Docker Compose stack, every
    session uses that token. Otherwise each visitor signs in with their own
    Infrahub account, so Infrahub applies that account's permissions. The page
    stops at the sign-in form until the visitor has signed in.
    """
    if INFRAHUB_API_TOKEN:
        return InfrahubClient(INFRAHUB_ADDRESS, api_token=INFRAHUB_API_TOKEN, ui_url=INFRAHUB_UI_URL)

    client: InfrahubClient | None = st.session_state.get(_CLIENT_KEY)
    if client is None:
        _show_sign_in_form()
        st.stop()
    _show_signed_in_account(client)
    return client


def _show_sign_in_form() -> None:
    st.title("Sign in")
    st.markdown(
        "Sign in with your Infrahub account. The Service Catalog makes changes in Infrahub "
        "with that account's permissions."
    )
    with st.form("infrahub-sign-in"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
    if not submitted:
        return
    if not username or not password:
        st.error("Enter a username and a password.")
        return

    client = InfrahubClient(INFRAHUB_ADDRESS, ui_url=INFRAHUB_UI_URL, username=username, password=password)
    try:
        client.sign_in()
    except InfrahubAPIError as exc:
        st.error(str(exc))
        return
    st.session_state[_CLIENT_KEY] = client
    st.rerun()


def _show_signed_in_account(client: InfrahubClient) -> None:
    st.sidebar.markdown(f"Signed in as **{client.username}**")
    if st.sidebar.button("Sign out"):
        del st.session_state[_CLIENT_KEY]
        st.rerun()
