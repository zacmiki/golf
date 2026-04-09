import streamlit as st

from modules.graphs import fig_companion
from modules.hcp_manager_page import load_coursetable
from modules.hcp_sim_page import hcp_sim
from modules.login_federgolf_selenium import extract_data, login
from modules.playing_hcp_page import playing_hcp

st.set_page_config(layout="wide")


# -------------------------
# Sidebar navigation
# -------------------------
def display_sidebar_menu():
    options = [
        "Official Rounds",
        "Handicap Manager",
        "Handicap Simulation",
        "Playing Handicap",
    ]

    st.sidebar.write("### Navigation")

    for option in options:
        if st.sidebar.button(option, use_container_width=True):
            st.session_state.selected_option = option

    if st.session_state.selected_option not in options:
        st.session_state.selected_option = options[0]


# -------------------------
# Login form
# -------------------------
def display_login_form():
    st.title("Login to Load Your F.I.G. Results")
    st.write("Please enter your username and password to download Your Results")
    username = st.text_input("Username", st.session_state.get("username", ""))
    password = st.text_input("Password", type="password")
    submit_button = st.button("Login")
    return username, password, submit_button


# -------------------------
# Logout handling
# -------------------------
def handle_logout():
    st.sidebar.write("---")
    logout_button = st.sidebar.button("Logout")
    if logout_button:
        # Clear all user-specific session state
        keys_to_clear = [
            "logged_in",
            "df",
            "federgolf_session",
            "username",
            "password",
            "tesserato_name",
            "tesserato_num",
            "profile_id",
            "current_handicap",
            "slider_value",
            "selected_option",
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        # Reset to defaults
        st.session_state.selected_option = "None"
        st.rerun()


# ---------------------   MAIN PAGE LOGIC --------------------
def main():
    # Initialize session states
    if "selected_option" not in st.session_state:
        st.session_state.selected_option = "None"
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "federgolf_session" not in st.session_state:
        st.session_state.federgolf_session = None

    # Sidebar menu
    st.sidebar.title("Your FederGolf Companion")
    st.sidebar.caption("By Mic&Jac Zac")
    st.sidebar.write("Please select an option from the sidebar.")

    display_sidebar_menu()

    # -------------------------
    # Handle login
    # -------------------------
    if not st.session_state.logged_in:
        username, password, submit_button = display_login_form()

        if submit_button:
            if username and password:
                st.session_state.username = username
                st.session_state.password = password
                with st.spinner("Logging in..."):
                    logged_in = login(username, password)
                    if logged_in:
                        st.session_state.logged_in = True
                        st.session_state.selected_option = "Handicap Manager"
                        st.rerun()
                    else:
                        st.error("Login failed. Please check your credentials.")
            else:
                st.error("Please enter both username and password.")
    else:
        # -------------------------
        # Load data if not already cached
        # -------------------------
        if st.session_state.selected_option in [
            "Official Rounds",
            "Handicap Manager",
            "Handicap Simulation",
            "Playing Handicap",
        ]:
            if "df" not in st.session_state or st.session_state.df is None:
                with st.spinner("Fetching data..."):
                    session = st.session_state.get("federgolf_session")
                    st.session_state.df = extract_data(session)

        # -------------------------
        # Render pages
        # -------------------------
        if st.session_state.selected_option == "Official Rounds":
            fig_companion()
        elif st.session_state.selected_option == "Handicap Manager":
            load_coursetable(st.session_state.df)
        elif st.session_state.selected_option == "Handicap Simulation":
            hcp_sim()
        elif st.session_state.selected_option == "Playing Handicap":
            playing_hcp()
        else:
            st.write("Please select an option from the sidebar.")

        handle_logout()

    # -------------------------
    # Footer / coffee link
    # -------------------------
    st.sidebar.divider()
    st.sidebar.markdown(
        """
    <a href="https://buymeacoffee.com/miczac?l=it" target="_blank">
        <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=YourUsername&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff">
    </a>
    """,
        unsafe_allow_html=True,
    )


# -------------------------
# Run app
# -------------------------
if __name__ == "__main__":
    main()
