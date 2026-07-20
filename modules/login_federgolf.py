from __future__ import annotations

import pandas as pd
import streamlit as st

from .federgolf_client import FederGolfError, MemberClient


def login(username: str, password: str) -> bool:
    """Authenticate without persisting credentials in state or on disk."""
    client = MemberClient()
    try:
        client.authenticate(username, password)
    except FederGolfError as exc:
        st.error(str(exc))
        return False

    st.session_state.federgolf_client = client
    st.session_state.tesserato_name = client.player_name
    return True


def extract_data(client: MemberClient | None) -> pd.DataFrame | None:
    if client is None:
        st.error("No authenticated session is available. Please log in again.")
        return None
    try:
        results = client.get_results()
    except FederGolfError as exc:
        st.error(str(exc))
        return None

    st.session_state.tesserato_name = results.player_name
    st.session_state.tesserato_num = results.membership_number
    st.session_state.current_handicap = results.current_handicap
    return results.dataframe
