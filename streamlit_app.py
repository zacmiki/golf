import streamlit as st

from modules.graphs import fig_companion
from modules.hcp_manager_page import load_coursetable
from modules.hcp_sim_page import hcp_sim
from modules.playing_hcp_page import playing_hcp

# Import the new login/extract_data module
from modules.login_federgolf_selenium import login, extract_data  # updated module

st.set_page_config(layout="wide")

# -------------------------
# Sidebar button helper
# -------------------------
def sidebar_button(label):
    button_html = f"""
    <style>
        div.stButton > button {{
            width: 100%;
        }}
    </style>
    """
    st.sidebar.markdown(button_html, unsafe_allow_html=True)
    return st.sidebar.button(label)

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
        st.session_state.pop("logged_in", None)
        st.session_state.pop("df", None)
        st.session_state.pop("federgolf_session", None)
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
    
    if sidebar_button("Official Rounds"):
        st.session_state.selected_option = "Official Rounds"
    if sidebar_button("Handicap Manager"):
        st.session_state.selected_option = "Handicap Manager"
    if sidebar_button("Handicap Simulation"):
        st.session_state.selected_option = "Handicap Simulation"
    if sidebar_button("Playing Handicap"):
        st.session_state.selected_option = "Playing Handicap"

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
                    session = login_and_get_session(username, password)
                    if session:
                        st.session_state.federgolf_session = session
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
            "Official Rounds", "Handicap Manager", "Handicap Simulation", "Playing Handicap"
        ]:
            if "df" not in st.session_state or st.session_state.df is None:
                with st.spinner("Fetching data..."):
                    st.session_state.df = extract_data(st.session_state.federgolf_session)

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
