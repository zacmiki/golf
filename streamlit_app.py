import streamlit as st

from modules.graphs import fig_companion
from modules.hcp_manager_page import load_coursetable
from modules.hcp_sim_page import hcp_sim
from modules.login_federgolf import extract_data, login

# Define a function to display the login form
def display_login_form():
    st.title("Login to Load Your F.I.G. Results")
    st.write("Please enter your username and password to download Your Results")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submit_button = st.button("Login")
    return username, password, submit_button

# Define a function to handle logout
def handle_logout():
    st.sidebar.write("---")
    logout_button = st.sidebar.button("Logout")
    if logout_button:
        st.session_state.pop("logged_in", None)
        st.session_state.pop("df", None)
        st.session_state.selected_option = "None"
        st.rerun()

# Function to set the button style
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

# ---------------------   MAIN PAGE LOGIC --------------------
# Main app logic
def main():
    # Initialize the selected_option state if not set
    if "selected_option" not in st.session_state:
        st.session_state.selected_option = "None"
    
    # Initialize the logged_in state if not set
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

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
    
    # Check if the user has already logged in
    if not st.session_state.logged_in:
        username, password, submit_button = display_login_form()

        if submit_button:
            if username and password:
                st.session_state.logged_in = login(username, password)

                if st.session_state.logged_in:
                    st.session_state.selected_option = "Handicap Manager"  # Set default to Handicap Manager
                    st.rerun()
                else:
                    st.error(
                        "Please enter a valid Username and Password. Something went wrong."
                    )
            else:
                st.error("Please enter both username and password.")
    else:
        if st.session_state.selected_option == "Official Rounds":
            # Make the request to extract the data
            if "df" not in st.session_state or st.session_state.df.empty:
                st.session_state.df = extract_data()

            # Plot everything for this page
            fig_companion()

            # Add a logout button in the sidebar
            handle_logout()

        elif st.session_state.selected_option == "Handicap Simulation":
            if "df" not in st.session_state or st.session_state.df.empty:
                st.session_state.df = extract_data()

            # User has already logged in, display the handicap visualizer
            hcp_sim()

            # Add a logout button in the sidebar
            handle_logout()

        elif st.session_state.selected_option == "Handicap Manager":
            if "df" not in st.session_state or st.session_state.df.empty:
                st.session_state.df = extract_data()

            # User has already logged in, display the handicap visualizer
            load_coursetable(st.session_state.df)

            # Add a logout button in the sidebar
            handle_logout()
        else:
            st.write("Please select an option from the sidebar.")


    st.sidebar.divider()
    st.sidebar.markdown(
    """
    <a href="https://buymeacoffee.com/miczac?l=it" target="_blank">
        <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=YourUsername&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff">
    </a>
    """,
    unsafe_allow_html=True,
    )   

# Set up the sidebar

if __name__ == "__main__":
    main()
