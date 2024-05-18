import pandas as pd
import streamlit as st

from modules.course_hcp import handicap_request
from modules.graphs import *
from modules.hcp_functions import *
from modules.login_federgolf import extract_data, login

# Set up the sidebar
st.sidebar.title("Your FederGolf Companion")
st.sidebar.caption("By The Zacs")
st.sidebar.write("Please select an option from the sidebar.")


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
        st.rerun()


# Main app logic
def main():
    selected_option = st.sidebar.selectbox(
        "Select an option",
        [
            "Your Rounds Graphs",
            "Your Handicap Manager",
        ],
    )

    # Initialize the logged_in state if not set
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # Check if the user has already logged in
    if not st.session_state.logged_in:
        username, password, submit_button = display_login_form()

        if submit_button:
            if username and password:
                st.session_state.logged_in = login(username, password)

                if st.session_state.logged_in:
                    st.rerun()
                else:
                    st.error(
                        "Please enter a valid Username and Password. Something went wrong."
                    )
            else:
                st.error("Please enter both username and password.")
    else:
        if selected_option == "Your Rounds Graphs":
            # Make the request to extract the data
            if "df" not in st.session_state or st.session_state.df.empty:
                st.session_state.df = extract_data()

            fig_companion(st.session_state.df)

            # Add a logout button in the sidebar
            handle_logout()

        elif selected_option == "Your Handicap Manager":
            if "df" not in st.session_state or st.session_state.df.empty:
                st.session_state.df = extract_data()

            # User has already logged in, display the handicap visualizer
            loadcoursetable(st.session_state.df)

            # Make the request with the two possible parameters
            handicap_request()

            # Add a logout button in the sidebar
            handle_logout()

        else:
            pass


# ------------- Visualization Page ------ F.I.G. Session -----------
def fig_companion(df):

    plot_type_mapping = {
        "Line Area Plot": "line",
        "Bar Chart": "bar",
        "Scatter Plot": "scatter",
    }

    st.title("Official FederGolf Results")
    st.markdown("Handicap Visualizer ... and more ...")
    st.divider()

    current_handicap = df["Index Nuovo"][0]
    best_handicap = df["Index Nuovo"].min()
    st.subheader(f"Tesserato {df['Tesserato'][0]}")
    st.markdown(
        "Your Current HCP is: {} - Best handicap: {}".format(
            current_handicap, best_handicap
        )
    )

    st.subheader(f" Slider to select the number of results")

    # User has already logged in, display the handicap visualizer
    slider_value = st.slider("Select the number of results:", 1, 100, 20)

    st.subheader("Plot of your Handicap progression")
    st.markdown(f"Showing last {slider_value} results:")
    plot_type_options = list(plot_type_mapping.keys())
    selected_plot_type = st.selectbox("Choose a plot type", plot_type_options)

    plot_last_n(
        df, slider_value, plot_type=plot_type_mapping.get(selected_plot_type, "line")
    )

    # st.header("Strokes in the Last {} Rounds".format(slider_value))
    st.subheader(f"Strokes Distribution [Last {slider_value} Rounds]")
    plot_gaussian = st.checkbox("Plot Gaussian")
    histo_n(df, plot_gaussian, slider_value)

    st.subheader("Last Rounds Data [Downloadable CSV]")
    st.markdown(f"Dataframe of the last: {slider_value} rounds:")
    st.write(df.iloc[-slider_value:])


if __name__ == "__main__":
    main()
