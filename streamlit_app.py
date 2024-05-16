import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from modules.graphs import *
from modules.login_federgolf import login
from modules.hcp_functions import *

# Set up the sidebar
st.sidebar.title("Your FederGolf Companion")
st.sidebar.caption("By Zac")
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
        st.session_state.pop("df", None)
        st.rerun()

# Main app logic
def main():
    selected_option = st.sidebar.selectbox(
        "Select an option",
        [
            "Data Visualization",
            "HCP Manager",
        ],
    )

    # Check if the user has already logged in
    if "df" not in st.session_state:
        username, password, submit_button = display_login_form()
        login_attempt = False

        if submit_button:
            login_attempt, df = login(username, password)

            if login_attempt:
                st.session_state["df"] = df
                st.rerun()
            else:
                st.write(
                    "Please enter both username and password. Something went wrong."
                )
    else:
        if selected_option == "Data Visualization":
            # User has already logged in, display the handicap visualizer
            slider_value = st.sidebar.slider(
                "Select the number of results:", 1, 100, 20
            )
            fig_companion(st.session_state.df, slider_value)

            # Add a logout button in the sidebar
            handle_logout()

        elif selected_option == "HCP Manager":
                # User has already logged in, display the handicap visualizer
                loadcoursetable(st.session_state.df)
                # Add a logout button in the sidebar
                handle_logout()

        else:
            pass

# ------------- Visualization Page ------ F.I.G. Session -----------

def fig_companion(df, slider_value):

    plot_type_mapping = {
        "Histogram": "histogram",
        "Scatter Plot": "scatter",
        "Line Plot": "line",
        "Bar Chart": "bar",
    }

    st.title("Official FederGolf Results")
    st.write("Hcp Visualizer - and more services still to come ...")
    st.divider()

    current_handicap = df["Index Nuovo"][0]
    best_handicap = df["Index Nuovo"].min()
    st.subheader(f"Tesserato {df['Tesserato'][0]}")
    st.markdown(
        "Your Current HCP is: {} - Best handicap: {}".format(
            current_handicap, best_handicap
        )
    )

    st.subheader("Plot of your Handicap progression")
    st.markdown(f"Showing last {slider_value} results:")
    plot_last_n(df, slider_value)

    # st.header("Strokes in the Last {} Rounds".format(slider_value))
    st.subheader("Strokes in the Last Rounds")
    plot_gaussian = st.checkbox("Plot Gaussian")
    # bar_plot_n(df, plot_gaussian, slider_value)
    histo_n(df, plot_gaussian, slider_value)

    # Future ideas
    # graph_last_n(df, slider_value, plot_type_mapping[selected_plot_type])
    # plot_type_options = list(plot_type_mapping.keys())
    # selected_plot_type = st.selectbox("Choose a plot type:", plot_type_options)
    # graph_last_n(df, slider_value, plot_type_mapping[selected_plot_type])

    st.subheader("Last Rounds - All Your Data [Downloadable CSV]".format(slider_value))
    st.markdown(f"Dataframe of the last: {slider_value} rounds:")
    st.write(df.iloc[-slider_value:])


if __name__ == "__main__":
    main()
