from __future__ import annotations

from importlib import import_module

import streamlit as st

from modules.ui import sidebar_footer

st.set_page_config(layout="wide")


PAGES = {
    "Official Rounds": ("modules.rounds_page", "official_rounds"),
    "Performance Insights": ("modules.insights_page", "performance_insights"),
    "Handicap Manager": ("modules.hcp_manager_page", "handicap_manager"),
    "Handicap Simulation": ("modules.hcp_sim_page", "hcp_sim"),
    "Course Handicap": ("modules.playing_hcp_page", "playing_hcp"),
}


def render_page(name: str) -> None:
    module_name, function_name = PAGES.get(name, PAGES["Official Rounds"])
    getattr(import_module(module_name), function_name)()


def initialize_state() -> None:
    defaults = {
        "selected_option": "Official Rounds",
        "logged_in": False,
        "federgolf_client": None,
        "df": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def sidebar() -> None:
    st.sidebar.title("Your FederGolf Companion")
    st.sidebar.caption("By Mic&Jac Zac")
    st.sidebar.subheader("Navigation")
    for page in PAGES:
        if st.sidebar.button(page, width="stretch"):
            st.session_state.selected_option = page


def login_page() -> None:
    st.title("Login to FederGolf")
    st.write("Enter your FederGolf credentials to load your official results.")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if not submitted:
        return
    if not username or not password:
        st.error("Please enter both username and password.")
        return
    from modules.login_federgolf import login

    with st.spinner("Logging in..."):
        if login(username, password):
            st.session_state.logged_in = True
            st.session_state.selected_option = "Handicap Manager"
            st.rerun()


def load_results() -> bool:
    if st.session_state.df is not None:
        return True
    from modules.login_federgolf import extract_data

    with st.spinner("Fetching results..."):
        st.session_state.df = extract_data(st.session_state.federgolf_client)
    if st.session_state.df is None or st.session_state.df.empty:
        st.error("No usable FederGolf results were returned. Please log in again.")
        return False
    return True


def logout() -> None:
    st.session_state.clear()


def main() -> None:
    initialize_state()
    sidebar()

    if not st.session_state.logged_in:
        login_page()
    elif load_results():
        render_page(st.session_state.selected_option)
        st.sidebar.button("Logout", on_click=logout, width="stretch")

    sidebar_footer()


if __name__ == "__main__":
    main()
